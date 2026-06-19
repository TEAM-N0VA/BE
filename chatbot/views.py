import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionCreateSerializer,
    ChatSessionListSerializer,
    ChatMessageSerializer,
    ChatRequestSerializer,
)


class ChatSessionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 20))

        qs = ChatSession.objects.filter(user=request.user)
        total = qs.count()
        offset = (page - 1) * size
        sessions = qs[offset:offset + size]

        serializer = ChatSessionListSerializer(sessions, many=True)
        return Response({
            'code': 'OK',
            'data': {
                'items': serializer.data,
                'total': total,
                'page': page,
                'size': size,
            }
        })

    def post(self, request):
        serializer = ChatSessionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        session = ChatSession.objects.create(
            user=request.user,
            locale=serializer.validated_data.get('locale', 'ko'),
        )

        return Response({
            'code': 'OK',
            'data': {
                'session_id': session.id,
                'started_at': session.started_at.isoformat(),
            }
        }, status=status.HTTP_201_CREATED)


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        session_id = data['session_id']
        content = data['content']

        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {'code': 'NOT_FOUND', 'message': '채팅 세션을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if session.ended_at:
            return Response(
                {'code': 'SESSION_ENDED', 'message': '종료된 세션입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save user message
        user_msg = ChatMessage.objects.create(
            session=session,
            role='user',
            content=content,
            rag_sources=[],
        )

        # Call AI server for response
        ai_server_url = getattr(settings, 'AI_SERVER_URL', '')
        if not ai_server_url:
            return Response(
                {'code': 'AI_SERVER_NOT_CONFIGURED', 'message': 'AI 서버가 설정되지 않았습니다.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Gather recent messages for context
        recent_messages = list(
            session.messages.order_by('-created_at')[:10]
        )
        recent_messages.reverse()
        message_history = [
            {'role': m.role, 'content': m.content}
            for m in recent_messages
        ]

        try:
            resp = requests.post(
                f"{ai_server_url}/chatbot/chat",
                json={
                    'session_id': session_id,
                    'user_id': request.user.id,
                    'content': content,
                    'history': message_history,
                    'locale': session.locale,
                },
                timeout=30,
            )
            resp.raise_for_status()
            ai_result = resp.json()
        except requests.RequestException as e:
            return Response(
                {'code': 'AI_SERVER_ERROR', 'message': f'AI 서버와 통신 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Save assistant message
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_result.get('content', ''),
            rag_sources=ai_result.get('rag_sources', []),
        )

        return Response({
            'code': 'OK',
            'data': {
                'message_id': assistant_msg.id,
                'role': assistant_msg.role,
                'content': assistant_msg.content,
                'rag_sources': assistant_msg.rag_sources,
                'created_at': assistant_msg.created_at.isoformat(),
            }
        })


class ChatSessionMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {'code': 'NOT_FOUND', 'message': '채팅 세션을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        messages = session.messages.order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True)

        return Response({
            'code': 'OK',
            'data': {
                'session_id': session.id,
                'messages': serializer.data,
            }
        })


class ChatSessionDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return Response(
                {'code': 'NOT_FOUND', 'message': '채팅 세션을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Mark as ended rather than deleting (preserve history)
        session.ended_at = timezone.now()
        session.save(update_fields=['ended_at'])
        session.messages.all().delete()

        return Response({'code': 'OK', 'message': '채팅 세션이 삭제되었습니다.'})
