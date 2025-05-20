"""
ASGI config for socialconnect project.
It exposes the ASGI callable as a module-level variable named `application`.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialconnect.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

import SocialProject.routing  # Import routing after Django setup

application = ProtocolTypeRouter({
    # Django's ASGI application for traditional HTTP requests
    "http": django_asgi_app,

    # WebSocket handler with authentication and URL routing
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                SocialProject.routing.websocket_urlpatterns
            )
        )
    ),
})
