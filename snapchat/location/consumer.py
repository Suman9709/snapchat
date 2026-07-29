import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q

from snapchat.models import FriendRequest, UserLocation


class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_group_name = f"location_{self.user.id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()
        await self.send_friend_locations()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get("type") == "get_friend_locations":
            await self.send_friend_locations()
            return

        latitude = data.get("latitude")
        longitude = data.get("longitude")
        if latitude is None or longitude is None:
            return

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return

        await self.save_location(latitude, longitude)
        updated_at = await self.get_my_location_updated_at()

        event = {
            "type": "location_update",
            "user_id": self.user.id,
            "username": self.user.username,
            "profile_pic": self.get_profile_pic_url(self.user),
            "latitude": latitude,
            "longitude": longitude,
            "updated_at": updated_at,
        }

        for friend_id in await self.get_friend_ids():
            await self.channel_layer.group_send(
                f"location_{friend_id}",
                event,
            )

        await self.send(
            text_data=json.dumps({
                "type": "location_saved",
                "latitude": latitude,
                "longitude": longitude,
                "updated_at": updated_at,
            })
        )

    async def location_update(self, event):
        await self.send(
            text_data=json.dumps({
                "type": "location",
                "user_id": event["user_id"],
                "username": event["username"],
                "profile_pic": event.get("profile_pic"),
                "latitude": event["latitude"],
                "longitude": event["longitude"],
                "updated_at": event.get("updated_at"),
            })
        )

    async def send_friend_locations(self):
        await self.send(
            text_data=json.dumps({
                "type": "friends_locations",
                "locations": await self.get_friend_locations(),
            })
        )

    @database_sync_to_async
    def save_location(self, latitude, longitude):
        UserLocation.objects.update_or_create(
            user=self.user,
            defaults={
                "latitude": latitude,
                "longitude": longitude,
            },
        )

    @database_sync_to_async
    def get_my_location_updated_at(self):
        location = UserLocation.objects.get(user=self.user)
        return location.updated_at.isoformat()

    @database_sync_to_async
    def get_friend_ids(self):
        friend_requests = FriendRequest.objects.filter(
            Q(from_user=self.user) | Q(to_user=self.user),
            status=FriendRequest.StatusChoices.ACCEPTED,
        ).select_related("from_user", "to_user")

        return [
            friend_request.to_user_id
            if friend_request.from_user_id == self.user.id
            else friend_request.from_user_id
            for friend_request in friend_requests
        ]

    @database_sync_to_async
    def get_friend_locations(self):
        friend_requests = FriendRequest.objects.filter(
            Q(from_user=self.user) | Q(to_user=self.user),
            status=FriendRequest.StatusChoices.ACCEPTED,
        ).select_related(
            "from_user",
            "to_user",
            "from_user__location",
            "to_user__location",
        )

        locations = []
        for friend_request in friend_requests:
            friend = (
                friend_request.to_user
                if friend_request.from_user_id == self.user.id
                else friend_request.from_user
            )
            location = getattr(friend, "location", None)
            if not location:
                continue

            locations.append({
                "user_id": friend.id,
                "username": friend.username,
                "profile_pic": self.get_profile_pic_url(friend),
                "latitude": location.latitude,
                "longitude": location.longitude,
                "updated_at": location.updated_at.isoformat(),
            })

        return locations

    def get_profile_pic_url(self, user):
        if not user.profile_pic:
            return None

        return user.profile_pic.url
