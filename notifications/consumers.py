import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""

    async def connect(self):
        """Connect to the notification channel"""
        self.user = self.scope['user']

        # Anonymous users can't receive notifications
        if not self.user.is_authenticated:
            await self.close()
            return

        # Create a personal notification group for the user
        self.notification_group_name = f'notifications_{self.user.id}'

        # Join the notification group
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """Disconnect from the notification channel"""
        # Leave notification group
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )

    async def notification_message(self, event):
        """Send notification to WebSocket"""
        # Send the notification message to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))

    @classmethod
    async def send_notification(cls, user_id, notification_data):
        """Send notification to the user's group"""
        notification_group_name = f'notifications_{user_id}'

        # Import inside the method to avoid circular import
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        # Send notification to the group
        await channel_layer.group_send(
            notification_group_name,
            {
                'type': 'notification_message',
                'notification': notification_data
            }
        )

    @staticmethod
    @database_sync_to_async
    def get_user(user_id):
        """Get a user by ID"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    @database_sync_to_async
    def create_notification(recipient, sender, notification_type, text, post=None, comment=None):
        """Create a notification in the database"""
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            text=text,
            post=post,
            comment=comment
        )
        return notification