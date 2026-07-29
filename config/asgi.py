import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from snapchat.location.routing import websocket_urlpatterns as location_websocket_urlpatterns
from snapchat.routing import websocket_urlpatterns as chat_websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(chat_websocket_urlpatterns + location_websocket_urlpatterns)
        ),
    }
)
