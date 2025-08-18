# apps/conversations/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/conversations/$', consumers.ConversationConsumer.as_asgi()),
    re_path(r'ws/agent/(?P<agent_id>[^/]+)/$', consumers.AgentConsumer.as_asgi()),
    re_path(r'ws/organization/$', consumers.OrganizationConsumer.as_asgi()),

]