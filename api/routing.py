from django.urls import re_path
from .consumers import StreamConsumer

websocket_urlpatterns = [
    re_path(r'ws/ai/stream/$', StreamConsumer.as_asgi()),
]