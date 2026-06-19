from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatSessionCreateSerializer(serializers.Serializer):
    locale = serializers.CharField(max_length=10, default='ko', required=False)


class ChatSessionListSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source='id', read_only=True)
    last_message_preview = serializers.CharField(read_only=True)
    message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ChatSession
        fields = ['session_id', 'started_at', 'ended_at', 'last_message_preview', 'message_count']


class ChatMessageSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['message_id', 'role', 'content', 'rag_sources', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    content = serializers.CharField()
