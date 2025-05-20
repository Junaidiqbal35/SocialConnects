from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm


def signup(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('feed:home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Authenticate and login the user
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request,
                             f"Welcome to SocialConnect, {username}! Your account has been created successfully.")
            return redirect('profiles:edit')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})