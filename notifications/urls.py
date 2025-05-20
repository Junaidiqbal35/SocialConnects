from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('mark_as_read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    path('mark_as_read_ajax/<int:notification_id>/', views.mark_as_read_ajax, name='mark_as_read_ajax'),
    path('count/', views.notification_count, name='count'),
]