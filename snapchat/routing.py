from django.urls import re_path
from .consumers import ChatConsume, NotificationConsume

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", NotificationConsume.as_asgi()),
    re_path(
        r"ws/chat/(?P<conversation_id>\d+)/$",
        ChatConsume.as_asgi(),
    ),
]