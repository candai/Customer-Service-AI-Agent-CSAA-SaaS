"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os
import django
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')

# if DEBUG:
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.development")
# else:
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")

# Initialize Django BEFORE importing anything else
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Initialize Django ASGI application early to ensure settings are loaded
django_asgi_app = get_asgi_application()

# Now import your routing and middleware AFTER Django is setup
from apps.conversations.routing import websocket_urlpatterns
from apps.conversations.middleware import JWTAuthMiddleware
from .settings import base as settings

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
    django_asgi_app = ASGIStaticFilesHandler(django_asgi_app)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})

logger.info("ASGI application configured")
