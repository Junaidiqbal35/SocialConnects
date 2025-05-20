from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify
import os


def user_avatar_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/avatars/user_<id>/<filename>
    ext = filename.split('.')[-1]
    new_filename = f"avatar.{ext}"
    return f"avatars/user_{instance.user.id}/{new_filename}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to=user_avatar_path, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    website = models.URLField(max_length=200, blank=True)

    # Social media links
    facebook = models.URLField(max_length=200, blank=True)
    twitter = models.URLField(max_length=200, blank=True)
    instagram = models.URLField(max_length=200, blank=True)
    linkedin = models.URLField(max_length=200, blank=True)

    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)

    # Additional profile fields
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def get_absolute_url(self):
        return reverse('profiles:detail', kwargs={'username': self.user.username})

    def follow(self, profile):
        """Follow a profile if not already following"""
        if profile != self and profile not in self.following.all():
            self.following.add(profile)
            return True
        return False

    def unfollow(self, profile):
        """Unfollow a profile if following"""
        if profile in self.following.all():
            self.following.remove(profile)
            return True
        return False

    def is_following(self, profile):
        """Check if following a profile"""
        return profile in self.following.all()

    def get_followers_count(self):
        """Get count of followers"""
        return self.followers.count()

    def get_following_count(self):
        """Get count of profiles being followed"""
        return self.following.count()

    def save(self, *args, **kwargs):
        # Delete old avatar file when uploading a new one
        if self.pk:
            try:
                old_profile = Profile.objects.get(pk=self.pk)
                if old_profile.avatar and self.avatar and old_profile.avatar != self.avatar:
                    old_profile.avatar.delete(save=False)
            except Profile.DoesNotExist:
                pass
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create Profile when User is created"""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save Profile when User is saved"""
    instance.profile.save()