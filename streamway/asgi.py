"""
ASGI config for streamway project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'streamway.settings')
django.setup()  # Ensures Django apps are loaded for Channels
from communications import routers
from tenant.middleware import WebSocketTenantMiddleware



application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": WebSocketTenantMiddleware(  # Apply tenant middleware first
        AuthMiddlewareStack(  # Then auth middleware
            URLRouter(
                routers.websocket_urlpatterns
            )
        )
    ),
})

