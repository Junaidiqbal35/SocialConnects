import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Conversation, Message
from notifications.models import Notification


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat"""

    async def connect(self):
        """Connect to the chat room"""
        self.user = self.scope['user']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Reject connection if user is not authenticated
        if not self.user.is_authenticated:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """Disconnect from the chat room"""
        # Leave room group
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type', 'message')

        # Handle different message types
        if message_type == 'message':
            conversation_id = data['conversation_id']
            message = data['message']

            # Save message to database
            message_obj = await self.save_message(conversation_id, message)

            # Get the other participant in the conversation
            conversation = await self.get_conversation(conversation_id)
            if conversation:
                other_user = await self.get_other_participant(conversation.id, self.user.id)

                # Create notification for the other user
                if other_user:
                    notification = await self.create_notification(
                        recipient=other_user,
                        sender=self.user,
                        notification_type='message',
                        text=f"{self.user.username} sent you a message",
                    )

                    # Send a notification over the notification consumer if needed
                    # This would require importing the NotificationConsumer or using a service

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'message_id': str(message_obj.id),
                    'timestamp': message_obj.created_at.isoformat(),
                }
            )

        elif message_type == 'typing':
            # Send typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': data.get('is_typing', False)
                }
            )

        elif message_type == 'delete':
            # Handle message deletion
            message_id = data['message_id']

            # Delete message in database
            success = await self.delete_message(message_id, self.user.id)

            if success:
                # Notify room about message deletion
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_deleted',
                        'message_id': message_id,
                    }
                )

    async def chat_message(self, event):
        """Send message to WebSocket"""
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing'],
        }))

    async def message_deleted(self, event):
        """Send message deletion notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'delete',
            'message_id': event['message_id'],
        }))

    @database_sync_to_async
    def save_message(self, conversation_id, content):
        """Save a message to the database"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content
            )
            # Update conversation timestamp
            conversation.updated_at = message.created_at
            conversation.save()
            return message
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def get_conversation(self, conversation_id):
        """Get a conversation by ID"""
        try:
            return Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def get_other_participant(self, conversation_id, user_id):
        """Get the other participant in a conversation"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return conversation.participants.exclude(id=user_id).first()
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def delete_message(self, message_id, user_id):
        """Delete a message (soft delete)"""
        try:
            message = Message.objects.get(id=message_id, sender_id=user_id)
            message.soft_delete()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def create_notification(self, recipient, sender, notification_type, text):
        """Create a notification in the database"""
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            text=text
        )
        return notification