from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Post, Comment, SharedPost
from .forms import PostForm, CommentForm, SharePostForm
from notifications.models import Notification


@login_required
def home(request):
    """Homepage feed with posts from followed users"""
    # Get users that current user follows
    following_users = request.user.profile.following.values_list('user', flat=True)

    # Get posts from followed users and user's own posts
    posts = Post.objects.filter(
        Q(author__in=following_users) | Q(author=request.user)
    ).select_related('author', 'author__profile').prefetch_related('comments')

    # Get shared posts
    shared_posts = SharedPost.objects.filter(
        Q(shared_by__in=following_users) | Q(shared_by=request.user)
    ).select_related('original_post', 'shared_by', 'original_post__author')

    # Create a new post form
    form = PostForm()

    return render(request, 'feed/home.html', {
        'posts': posts,
        'shared_posts': shared_posts,
        'form': form
    })


@login_required
def create_post(request):
    """Create a new post"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Your post has been created!')
            return redirect('feed:home')
    else:
        form = PostForm()

    return render(request, 'feed/create_post.html', {'form': form})


@login_required
def post_detail(request, pk):
    """Detail view for a specific post with comments"""
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all().select_related('author', 'author__profile')
    comment_form = CommentForm()
    share_form = SharePostForm()

    return render(request, 'feed/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'share_form': share_form
    })


@login_required
def edit_post(request, pk):
    """Edit an existing post"""
    post = get_object_or_404(Post, pk=pk, author=request.user)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your post has been updated!')
            return redirect('feed:post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)

    return render(request, 'feed/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, pk):
    """Delete a post"""
    post = get_object_or_404(Post, pk=pk, author=request.user)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Your post has been deleted!')
        return redirect('feed:home')

    return render(request, 'feed/delete_post.html', {'post': post})


@login_required
@require_POST
def like_post(request, pk):
    """Like a post"""
    post = get_object_or_404(Post, pk=pk)
    post.likes.add(request.user)

    # Create notification for post author (if not self)
    if post.author != request.user:
        Notification.objects.create(
            recipient=post.author,
            sender=request.user,
            notification_type='like',
            post=post,
            text=f"{request.user.username} liked your post"
        )

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'likes_count': post.get_like_count()
        })

    return redirect('feed:post_detail', pk=pk)


@login_required
@require_POST
def unlike_post(request, pk):
    """Unlike a post"""
    post = get_object_or_404(Post, pk=pk)
    post.likes.remove(request.user)

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'likes_count': post.get_like_count()
        })

    return redirect('feed:post_detail', pk=pk)


@login_required
def share_post(request, pk):
    """Share/repost a post"""
    original_post = get_object_or_404(Post, pk=pk)

    if request.method == 'POST':
        form = SharePostForm(request.POST)
        if form.is_valid():
            shared_post = form.save(commit=False)
            shared_post.original_post = original_post
            shared_post.shared_by = request.user
            shared_post.save()

            # Create notification for original post author (if not self)
            if original_post.author != request.user:
                Notification.objects.create(
                    recipient=original_post.author,
                    sender=request.user,
                    notification_type='share',
                    post=original_post,
                    text=f"{request.user.username} shared your post"
                )

            messages.success(request, 'Post shared successfully!')
            return redirect('feed:home')
    else:
        form = SharePostForm()

    return render(request, 'feed/share_post.html', {
        'form': form,
        'post': original_post
    })


@login_required
@require_POST
def add_comment(request, post_pk):
    """Add a comment to a post"""
    post = get_object_or_404(Post, pk=post_pk)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()

        # Create notification for post author (if not self)
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notification_type='comment',
                post=post,
                comment=comment,
                text=f"{request.user.username} commented on your post"
            )

        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'author': comment.author.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%b %d, %Y, %I:%M %p'),
                'comments_count': post.get_comment_count()
            })
    else:
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)

    return redirect('feed:post_detail', pk=post_pk)


@login_required
def edit_comment(request, pk):
    """Edit a comment"""
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    post = comment.post

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your comment has been updated!')
            return redirect('feed:post_detail', pk=post.pk)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'feed/edit_comment.html', {
        'form': form,
        'comment': comment,
        'post': post
    })


@login_required
def delete_comment(request, pk):
    """Delete a comment"""
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    post = comment.post

    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Your comment has been deleted!')
        return redirect('feed:post_detail', pk=post.pk)

    return render(request, 'feed/delete_comment.html', {
        'comment': comment,
        'post': post
    })


@login_required
@require_POST
def like_comment(request, pk):
    """Like a comment"""
    comment = get_object_or_404(Comment, pk=pk)
    comment.likes.add(request.user)

    # Create notification for comment author (if not self)
    if comment.author != request.user:
        Notification.objects.create(
            recipient=comment.author,
            sender=request.user,
            notification_type='like_comment',
            post=comment.post,
            comment=comment,
            text=f"{request.user.username} liked your comment"
        )

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'likes_count': comment.get_like_count()
        })

    return redirect('feed:post_detail', pk=comment.post.pk)


@login_required
@require_POST
def unlike_comment(request, pk):
    """Unlike a comment"""
    comment = get_object_or_404(Comment, pk=pk)
    comment.likes.remove(request.user)

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'likes_count': comment.get_like_count()
        })

    return redirect('feed:post_detail', pk=comment.post.pk)