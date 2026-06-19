import requests
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import RecommendLog
from .serializers import (
    RecommendRequestSerializer,
    RecommendFeedbackSerializer,
    RecommendLogListSerializer,
)


class RecommendStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from blood_sugar.models import FoodSensitivity

        user = request.user
        sensitivities = FoodSensitivity.objects.filter(user=user).select_related('food_info')

        analysis_count = sensitivities.count()

        # Top safe foods: lowest avg_spike with at least some data
        top_safe = sensitivities.filter(sample_count__gt=0).order_by('avg_spike')[:5]
        top_safe_foods = [
            {'food_name': s.food_info.food_name, 'avg_spike': round(s.avg_spike, 2)}
            for s in top_safe
        ]

        # Sensitivity summary
        sensitivity_summary = []
        if sensitivities.exists():
            avg_spike_all = sum(s.avg_spike for s in sensitivities) / max(analysis_count, 1)
            # ai_learning_level: 0~100 float, 데이터 50건 이상이면 100
            ai_learning_level = round(min(100.0, analysis_count * 2.0), 1)

            if avg_spike_all < 20:
                sensitivity = '안정'
            elif avg_spike_all < 40:
                sensitivity = '주의'
            else:
                sensitivity = '위험'

            sensitivity_summary.append({
                'sensitivity': sensitivity,
                'frequent_category': '탄수화물',
                'ai_learning_level': ai_learning_level,
            })

        return Response({
            'code': 'OK',
            'data': {
                'analysis_count': analysis_count,
                'top_safe_foods': top_safe_foods,
                'sensitivity_summary': sensitivity_summary,
            }
        })


class RecommendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RecommendRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        ai_server_url = getattr(settings, 'AI_SERVER_URL', '')

        if not ai_server_url:
            return Response(
                {'code': 'AI_SERVER_NOT_CONFIGURED', 'message': 'AI 서버가 설정되지 않았습니다.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        payload = {
            'user_id': request.user.id,
            'meal_type': data['meal_type'],
            'context': data.get('context', {}),
        }

        try:
            resp = requests.post(
                f"{ai_server_url}/recommend",
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            ai_result = resp.json()
        except requests.RequestException as e:
            return Response(
                {'code': 'AI_SERVER_ERROR', 'message': f'AI 서버와 통신 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        recommend_log = RecommendLog.objects.create(
            user=request.user,
            meal_type=data['meal_type'],
            context=data.get('context', {}),
            result=ai_result.get('result', {}),
            reason=ai_result.get('reason', ''),
        )

        return Response({
            'code': 'OK',
            'data': {
                'recommend_id': recommend_log.id,
                'result': recommend_log.result,
                'reason': recommend_log.reason,
            }
        }, status=status.HTTP_201_CREATED)


class RecommendHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 20))

        qs = RecommendLog.objects.filter(user=request.user)
        total = qs.count()
        offset = (page - 1) * size
        items = qs[offset:offset + size]

        serializer = RecommendLogListSerializer(items, many=True)
        return Response({
            'code': 'OK',
            'data': {
                'items': serializer.data,
                'total': total,
                'page': page,
                'size': size,
            }
        })


class RecommendFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recommend_id):
        try:
            recommend_log = RecommendLog.objects.get(id=recommend_id, user=request.user)
        except RecommendLog.DoesNotExist:
            return Response(
                {'code': 'NOT_FOUND', 'message': '추천 기록을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RecommendFeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        if 'user_rating' in data:
            recommend_log.user_rating = data['user_rating']
        if 'is_applied' in data:
            recommend_log.is_applied = data['is_applied']
        recommend_log.save()

        return Response({
            'code': 'OK',
            'data': {
                'recommend_id': recommend_log.id,
                'user_rating': recommend_log.user_rating,
            }
        })
