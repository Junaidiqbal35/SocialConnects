from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Conversation(models.Model):
    """Model for a conversation between users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation {self.id} between {', '.join([user.username for user in self.participants.all()])}"

    def get_messages(self):
        """Get all messages in this conversation"""
        return self.messages.all()

    def get_last_message(self):
        """Get the last message in this conversation"""
        return self.messages.order_by('-created_at').first()

    def mark_as_read(self, user):
        """Mark all unread messages as read for a specific user"""
        self.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    def add_message(self, sender, content):
        """Add a new message to the conversation"""
        message = Message.objects.create(
            conversation=self,
            sender=sender,
            content=content
        )
        self.updated_at = timezone.now()
        self.save()
        return message

    def get_other_participant(self, user):
        """Get the other participant in a two-person conversation"""
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    """Model for messages within a conversation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)  # For message deletion feature
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def mark_as_read(self):
        """Mark the message as read"""
        if not self.is_read:
            self.is_read = True
            self.save()

    def soft_delete(self):
        """Soft delete a message by setting is_deleted flag"""
        self.is_deleted = True
        self.content = "This message was deleted"
        self.save()