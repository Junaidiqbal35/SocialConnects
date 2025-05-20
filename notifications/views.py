from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list(request):
    """List all user's notifications"""
    notifications = Notification.objects.filter(recipient=request.user)
    unread_count = notifications.filter(is_read=False).count()

    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications.filter(is_read=False).update(is_read=True)
        return redirect('notifications:list')

    return render(request, 'notifications/list.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def mark_as_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()

        # Redirect to related content
        if notification.notification_type == 'follow':
            return redirect('profiles:detail', username=notification.sender.username)
        elif notification.notification_type in ['like', 'comment', 'share']:
            return redirect('feed:post_detail', pk=notification.post.id)
        elif notification.notification_type == 'like_comment':
            return redirect('feed:post_detail', pk=notification.post.id)
        elif notification.notification_type == 'message':
            return redirect('chat:conversation', username=notification.sender.username)
        else:
            return redirect('notifications:list')

    except Notification.DoesNotExist:
        return redirect('notifications:list')


@login_required
def mark_as_read_ajax(request, notification_id):
    """Mark a notification as read via AJAX"""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()

        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)


@login_required
def notification_count(request):
    """Return the count of unread notifications for AJAX requests"""
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': unread_count})


def notification_count_context(request):
    """Context processor for notification count"""
    if request.user.is_authenticated:
        notification_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {'notification_count': notification_count}
    return {'notification_count': 0}