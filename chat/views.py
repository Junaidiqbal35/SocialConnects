from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q, Count, Max, F, Exists, OuterRef
from django.db.models.functions import Greatest
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Conversation, Message
from notifications.models import Notification


@login_required
def inbox(request):
    """Display user's message inbox"""
    # Get all conversations for the user with the latest message
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        latest_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)),
    ).order_by('-latest_message_time')

    # Additional information for each conversation
    for conversation in conversations:
        # Get the other participant
        conversation.other_user = conversation.get_other_participant(request.user)
        # Get the last message
        conversation.last_message = conversation.get_last_message()

    return render(request, 'chat/inbox.html', {
        'conversations': conversations,
    })


@login_required
def start_conversation(request, username):
    """Start a new conversation with a user or open existing one"""
    other_user = get_object_or_404(User, username=username)

    # Cannot start conversation with yourself
    if other_user == request.user:
        return redirect('chat:inbox')

    # Check if conversation already exists
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()

    # Create new conversation if it doesn't exist
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)

    return redirect('chat:conversation', conversation_id=conversation.id)


@login_required
def conversation_detail(request, conversation_id):
    """Display a conversation with its messages"""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )

    # Get the other participant
    other_user = conversation.get_other_participant(request.user)

    # Mark all messages as read
    conversation.mark_as_read(request.user)

    # Get messages for this conversation
    messages = conversation.get_messages()

    return render(request, 'chat/conversation.html', {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages,
    })


@login_required
def load_messages(request, conversation_id):
    """API endpoint to load messages for a conversation"""
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )

    # Get messages with optional pagination
    before_id = request.GET.get('before')
    limit = int(request.GET.get('limit', 50))

    messages_query = conversation.messages.order_by('-created_at')

    if before_id:
        try:
            before_message = Message.objects.get(id=before_id)
            messages_query = messages_query.filter(created_at__lt=before_message.created_at)
        except Message.DoesNotExist:
            pass

    messages = list(messages_query[:limit])
    messages.reverse()  # Chronological order

    # Mark messages as read
    unread_messages = [msg for msg in messages if not msg.is_read and msg.sender != request.user]
    for message in unread_messages:
        message.mark_as_read()

    # Format messages for JSON response
    messages_data = []
    for message in messages:
        messages_data.append({
            'id': str(message.id),
            'sender_id': message.sender.id,
            'sender_username': message.sender.username,
            'content': message.content,
            'is_deleted': message.is_deleted,
            'created_at': message.created_at.isoformat(),
            'is_mine': message.sender == request.user,
        })

    return JsonResponse({
        'messages': messages_data,
        'has_more': messages_query.count() > len(messages),
    })


@login_required
@require_POST
def delete_message(request, message_id):
    """Delete (soft delete) a message"""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    message.soft_delete()

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    # Redirect back to conversation
    return redirect('chat:conversation', conversation_id=message.conversation.id)