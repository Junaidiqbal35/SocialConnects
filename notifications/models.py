from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from feed.models import Post, Comment


class Notification(models.Model):
    """Model for user notifications"""
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('share', 'Share'),
        ('like_comment', 'Like Comment'),
        ('message', 'Message'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    text = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} {self.get_notification_type_display().lower()} notification to {self.recipient.username}"

    def mark_as_read(self):
        """Mark the notification as read"""
        self.is_read = True
        self.save()