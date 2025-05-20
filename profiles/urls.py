
from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('edit/', views.edit_profile, name='edit'),
    path('search/', views.search_profiles, name='search'),
    path('explore/', views.explore, name='explore'),
    path('follow/<str:username>/', views.follow_profile, name='follow'),
    path('unfollow/<str:username>/', views.unfollow_profile, name='unfollow'),
    path('<str:username>/followers/', views.followers_list, name='followers'),
    path('<str:username>/following/', views.following_list, name='following'),
    path('<str:username>/', views.profile_detail, name='detail'),
]