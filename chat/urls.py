from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('start/<str:username>/', views.start_conversation, name='start'),
    path('conversation/<uuid:conversation_id>/', views.conversation_detail, name='conversation'),
    path('conversation/<uuid:conversation_id>/messages/', views.load_messages, name='load_messages'),
    path('message/<uuid:message_id>/delete/', views.delete_message, name='delete_message'),
]