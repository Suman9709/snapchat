from django.urls import re_path
from .consumers import ChatConsume

websocket_urlpatterns = [
    re_path(
        r"ws/chat/(?P<conversation_id>\d+)/$",
        ChatConsume.as_asgi(),
    ),
]