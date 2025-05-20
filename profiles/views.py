from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from .models import Profile
from .forms import ProfileForm, UserForm
from feed.models import Post
from notifications.models import Notification


@login_required
def edit_profile(request):
    """Edit user profile information"""
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profiles:detail', username=request.user.username)
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

    return render(request, 'profiles/edit.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def profile_detail(request, username):
    """Display user profile"""
    user = get_object_or_404(User, username=username)
    profile = user.profile

    # Check if profile is private and not the owner or follower
    if profile.is_private and user != request.user and not request.user.profile.is_following(profile):
        return render(request, 'profiles/private_profile.html', {'profile': profile})

    # Get posts for the profile
    posts = Post.objects.filter(author=user).order_by('-created_at')

    # Get common followers
    if request.user.is_authenticated and request.user != user:
        common_followers = request.user.profile.following.filter(
            user__profile__in=profile.followers.all()
        ).select_related('user')[:5]
    else:
        common_followers = Profile.objects.none()

    return render(request, 'profiles/detail.html', {
        'profile': profile,
        'posts': posts,
        'common_followers': common_followers,
    })


@login_required
def search_profiles(request):
    """Search for profiles"""
    query = request.GET.get('q', '')
    profiles = []

    if query:
        profiles = Profile.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(bio__icontains=query)
        ).select_related('user').distinct()

    return render(request, 'profiles/search.html', {
        'profiles': profiles,
        'query': query
    })


@login_required
def explore(request):
    """Explore profiles (popular and suggested)"""
    # Popular profiles (most followers)
    popular_profiles = Profile.objects.annotate(
        follower_count=Count('followers')
    ).order_by('-follower_count')[:8]

    # Suggested profiles (not following yet)
    user_following = request.user.profile.following.all()
    suggested_profiles = Profile.objects.exclude(
        Q(user=request.user) | Q(pk__in=user_following)
    ).order_by('?')[:8]  # Random order

    return render(request, 'profiles/explore.html', {
        'popular_profiles': popular_profiles,
        'suggested_profiles': suggested_profiles
    })


@login_required
@require_POST
def follow_profile(request, username):
    """Follow a user profile"""
    user_to_follow = get_object_or_404(User, username=username)
    profile_to_follow = user_to_follow.profile

    success = request.user.profile.follow(profile_to_follow)

    if success:
        # Create notification for the user being followed
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            notification_type='follow',
            text=f"{request.user.username} started following you"
        )

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': success,
            'followers_count': profile_to_follow.get_followers_count()
        })

    return redirect('profiles:detail', username=username)


@login_required
@require_POST
def unfollow_profile(request, username):
    """Unfollow a user profile"""
    user_to_unfollow = get_object_or_404(User, username=username)
    profile_to_unfollow = user_to_unfollow.profile

    success = request.user.profile.unfollow(profile_to_unfollow)

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': success,
            'followers_count': profile_to_unfollow.get_followers_count()
        })

    return redirect('profiles:detail', username=username)


@login_required
def followers_list(request, username):
    """List users following this profile"""
    user = get_object_or_404(User, username=username)
    profile = user.profile

    # Check if profile is private and not the owner or follower
    if profile.is_private and user != request.user and not request.user.profile.is_following(profile):
        return render(request, 'profiles/private_profile.html', {'profile': profile})

    followers = profile.followers.all().select_related('user')

    return render(request, 'profiles/connections.html', {
        'profile': profile,
        'connections': followers,
        'connection_type': 'followers'
    })


@login_required
def following_list(request, username):
    """List users this profile is following"""
    user = get_object_or_404(User, username=username)
    profile = user.profile

    # Check if profile is private and not the owner or follower
    if profile.is_private and user != request.user and not request.user.profile.is_following(profile):
        return render(request, 'profiles/private_profile.html', {'profile': profile})

    following = profile.following.all().select_related('user')

    return render(request, 'profiles/connections.html', {
        'profile': profile,
        'connections': following,
        'connection_type': 'following'
    })