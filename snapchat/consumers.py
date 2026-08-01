from email.mime import image
import json
from json import JSONDecodeError

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from snapchat.utils import update_snap_streak
from .models import Conversation, Message
from django.utils import timezone
from datetime import timedelta

class ChatConsume(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f'chat_{self.conversation_id}'

        if not self.scope['user'].is_authenticated:
            await self.close()
            return
        

        if not await self.user_can_access_conversation():
            await self.close()
            return
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.set_online(self.scope["user"])
        
        await self.accept()
        print(f"Connected to room: {self.room_group_name}")
        
    async def disconnect(self, close_code):
        await self.set_offline(self.scope['user'])
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        print("Disconnected ")
    
    
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except JSONDecodeError:
            return

        user = self.scope["user"]
        username = user.username

        if data.get("screenshot"):
            text = f"{username} took a screenshot of the chat."
            saved_message = await self.save_message(text, is_system=True)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "screenshot_notification",
                    "message": text,
                    "username": username,
                    "sender_id": user.id,
                    "timestamp": saved_message["timestamp"],
                    "created_at": saved_message["created_at"],
                    "message_id": saved_message["id"],
                },
            )
            return

        message = data.get("message")
        image = data.get("image")
        message_id = data.get("message_id")
        # print("Full data:", data)
        # print("image :", image)

        if message_id:
            saved_message = await self.get_saved_message(message_id)
            if not saved_message:
                return
        else:
            if not message and not image:
                return
            saved_message = await self.save_message(message=message, image=image)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": saved_message["message"],
                "image": saved_message["image"],
                "username": username,
                "sender_id": user.id,
                "timestamp": saved_message["timestamp"],
                "created_at": saved_message["created_at"],
                "message_id": saved_message["id"],
                "is_system": False,
            },
        )
        print("MESSAGE SENT TO GROUP:", self.room_group_name)
        
    async def chat_message(self, event):
        print("CHAT MESSAGE EVENT:", event)
        await self.send(text_data=json.dumps({
            'message': event.get('message'),
            'image': event.get('image'),
            'username': event.get('username'),
            'sender_id': event.get('sender_id'),
            'timestamp': event.get('timestamp'),
            'created_at': event.get('created_at'),
            'message_id': event.get('message_id'),
            'is_system': event.get('is_system', False),
        }))
        

    @database_sync_to_async
    def set_online(self, user):
        user.is_online = True
        user.last_seen = timezone.now()
        user.save(update_fields=['is_online', 'last_seen'])
        
    @database_sync_to_async
    def set_offline(self, user):
        user.is_online = False
        user.last_seen = timezone.now()
        user.save(update_fields=['is_online', 'last_seen'])
        
        
    @database_sync_to_async   
    def save_message(self, message=None, image=None, is_system=False):
        conversation = Conversation.objects.get(id=self.conversation_id)
        
        chat_message = Message.objects.create(
            conversation=conversation,
            sender=self.scope['user'],
            image=image,
            message=message or "",
            is_system=is_system
            
        
        
        )
        if image:
           
            update_snap_streak(
            conversation,
            self.scope['user']
        )
        if conversation.mode == Conversation.Mode.AFTER_24HR:
            chat_message.expires_at = timezone.now() + timedelta(hours=24)
            chat_message.save(update_fields=['expires_at'])
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        return self.serialize_message(chat_message)

    @database_sync_to_async
    def get_saved_message(self, message_id):
        try:
            message = Message.objects.select_related("sender").get(
                id=message_id,
                conversation_id=self.conversation_id,
                sender=self.scope["user"],
                is_system=False,
            )
        except Message.DoesNotExist:
            return None

        return self.serialize_message(message)

    def serialize_message(self, message):
        return {
            "id": message.id,
            "message": message.message,
            "image": message.image.url if message.image else None,
            "timestamp": timezone.localtime(message.created_at).strftime("%H:%M"),
            "created_at": message.created_at.isoformat(),
        }

    @database_sync_to_async
    def user_can_access_conversation(self):
        return Conversation.objects.filter(
            id=self.conversation_id,
            participants=self.scope['user'],
        ).exists()


    async def screenshot_notification(self, event):
        await self.send(
        text_data=json.dumps(
            {
                "screenshot": True,
                "message": event["message"],
                "username": event.get("username"),
                "sender_id": event["sender_id"],
                "timestamp": event.get("timestamp"),
                "created_at": event.get("created_at"),
                "message_id": event.get("message_id"),
                "is_system": True,
            }
        )
    )
