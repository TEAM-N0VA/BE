from django.urls import path
from .views import (
    ChatSessionListCreateView,
    ChatView,
    ChatSessionMessagesView,
    ChatSessionDeleteView,
)

urlpatterns = [
    path('sessions', ChatSessionListCreateView.as_view(), name='chat-session-list-create'),
    path('chat', ChatView.as_view(), name='chat'),
    path('sessions/<int:session_id>/messages', ChatSessionMessagesView.as_view(), name='chat-session-messages'),
    path('sessions/<int:session_id>', ChatSessionDeleteView.as_view(), name='chat-session-delete'),
]
