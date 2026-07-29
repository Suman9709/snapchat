import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message
from django.utils import timezone
from datetime import timedelta

class ChatConsume(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id =(self.scope['url_route']['kwargs']['conversation_id'])
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
        await self.accept()
        print(f"Connected to room: {self.room_group_name}")
        
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        print("Disconnected ")
    
    
    
    async def receive(self, text_data):
        data = json.loads(text_data)

        user = self.scope["user"]
        username = user.username

    # Screenshot notification
        if data.get("screenshot"):
            text = f"{username} took a screenshot of the chat."

            await self.save_message(text, is_system=True)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                 "type": "screenshot_notification",
                    "message": text,
                    "sender_id": user.id,
                },
            )
            return

    # Normal message
        message = data.get("message")
        image = data.get("image")

        if not message and not image:
            return

        if not image:
         await self.save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "image": image,
                "username": username,
                "sender_id": user.id,
                "timestamp": timezone.localtime().strftime("%H:%M"),
            },
     )
        
    async def chat_message(self, event):
        message = event['message']
        image = event['image']
        username = event['username']
        sender_id = event['sender_id']
        timestamp = event['timestamp']
        await self.send(text_data=json.dumps({
            'message': message,
            'image':image,
            'username': username,
            'sender_id': sender_id,
            'screenshot': event.get('screenshot'),
            'timestamp': timestamp,
            'is_system': event.get('is_system', False),
            
        }))
        

        
    @database_sync_to_async   
    def save_message(self, message, is_system=False):
        conversation = Conversation.objects.get(id=self.conversation_id)
        
        chat_message = Message.objects.create(
            conversation=conversation,
            sender=self.scope['user'],
            message=message,
            is_system = is_system
        
        )
        if conversation.mode == Conversation.Mode.AFTER_24HR:
            chat_message.expires_at = timezone.now() + timedelta(hours=24)
            chat_message.save(update_fields=['expires_at'])

        conversation.save(update_fields=['updated_at'])

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
                "sender_id": event["sender_id"],
            }
        )
    )