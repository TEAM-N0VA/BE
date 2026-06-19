import requests
from django.conf import settings
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import BloodSugarLog, BloodSugarPrediction, calculate_risk_level
from .serializers import (
    BloodSugarLogSerializer,
    BloodSugarLogCreateSerializer,
    BloodSugarLogUpdateSerializer,
    BloodSugarPredictionRequestSerializer,
)


class BloodSugarLogListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        record_type = request.query_params.get('record_type')
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 50))

        qs = BloodSugarLog.objects.filter(user=request.user)

        if from_date:
            dt = parse_date(from_date)
            if dt:
                qs = qs.filter(measured_at__date__gte=dt)

        if to_date:
            dt = parse_date(to_date)
            if dt:
                qs = qs.filter(measured_at__date__lte=dt)

        if record_type:
            qs = qs.filter(record_type=record_type)

        total = qs.count()
        offset = (page - 1) * size
        items = qs[offset:offset + size]

        items_data = []
        for log in items:
            items_data.append({
                'id': log.id,
                'value': log.value,
                'measured_at': log.measured_at.isoformat(),
                'record_type': log.record_type,
                'risk_level': log.risk_level,
                'meal_log_id': log.meal_log_id,
                'memo': log.memo,
            })

        return Response({
            'code': 'OK',
            'data': {
                'items': items_data,
                'total': total,
                'page': page,
                'size': size,
            }
        })

    def post(self, request):
        serializer = BloodSugarLogCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        meal_log_id = data.get('meal_log_id')
        meal_log = None

        if meal_log_id:
            from meals.models import MealLog
            try:
                meal_log = MealLog.objects.get(id=meal_log_id, user=request.user)
            except MealLog.DoesNotExist:
                return Response(
                    {'code': 'NOT_FOUND', 'message': '식사 기록을 찾을 수 없습니다.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        log = BloodSugarLog.objects.create(
            user=request.user,
            value=data['value'],
            measured_at=data['measured_at'],
            record_type=data['record_type'],
            meal_log=meal_log,
            memo=data.get('memo', ''),
        )

        # Check if sensitivity should be updated (simple heuristic)
        sensitivity_updated = False
        warning = None
        if log.risk_level == '위험':
            warning = f"혈당이 위험 수준입니다 ({log.value} mg/dL). 의사와 상담하세요."

        return Response({
            'code': 'OK',
            'data': {
                'id': log.id,
                'value': log.value,
                'risk_level': log.risk_level,
                'measured_at': log.measured_at.isoformat(),
                'sensitivity_updated': sensitivity_updated,
                'warning': warning,
            }
        }, status=status.HTTP_201_CREATED)


class BloodSugarLogDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_log(self, request, log_id):
        try:
            return BloodSugarLog.objects.get(id=log_id, user=request.user)
        except BloodSugarLog.DoesNotExist:
            return None

    def put(self, request, log_id):
        log = self._get_log(request, log_id)
        if not log:
            return Response(
                {'code': 'NOT_FOUND', 'message': '혈당 기록을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BloodSugarLogUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        if 'value' in data:
            log.value = data['value']
        if 'measured_at' in data:
            log.measured_at = data['measured_at']
        if 'record_type' in data:
            log.record_type = data['record_type']
        if 'memo' in data:
            log.memo = data['memo']

        log.save()

        return Response({
            'code': 'OK',
            'data': {
                'id': log.id,
                'value': log.value,
                'measured_at': log.measured_at.isoformat(),
                'record_type': log.record_type,
                'risk_level': log.risk_level,
                'memo': log.memo,
            }
        })

    def delete(self, request, log_id):
        log = self._get_log(request, log_id)
        if not log:
            return Response(
                {'code': 'NOT_FOUND', 'message': '혈당 기록을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
        log.delete()
        return Response({'code': 'OK', 'message': '혈당 기록이 삭제되었습니다.'})


class BloodSugarPredictionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BloodSugarPredictionRequestSerializer(data=request.data)
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

        # Build payload for AI server
        payload = {
            'fasting_glucose': data.get('fasting_glucose'),
            'meal_log_id': data.get('meal_log_id'),
            'planned_items': data.get('planned_items', []),
            'user_id': request.user.id,
        }

        try:
            resp = requests.post(
                f"{ai_server_url}/blood-sugar/predict",
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

        # Save prediction to DB
        meal_log = None
        meal_log_id = data.get('meal_log_id')
        if meal_log_id:
            from meals.models import MealLog
            try:
                meal_log = MealLog.objects.get(id=meal_log_id, user=request.user)
            except MealLog.DoesNotExist:
                pass

        prediction = BloodSugarPrediction.objects.create(
            user=request.user,
            meal_log=meal_log,
            fasting_glucose=data.get('fasting_glucose'),
            predicted_value=ai_result.get('predicted_value', 0),
            post_1h_glucose=ai_result.get('post_1h_glucose'),
            post_2h_glucose=ai_result.get('post_2h_glucose'),
            risk_level=ai_result.get('risk_level', '안전'),
            confidence=ai_result.get('confidence'),
            advice=ai_result.get('advice', ''),
            model_mode=ai_result.get('model_mode', ''),
        )

        # Update meal log predicted_glucose
        if meal_log:
            meal_log.predicted_glucose = prediction.predicted_value
            meal_log.save(update_fields=['predicted_glucose'])

        return Response({
            'code': 'OK',
            'data': {
                'predicted_value': prediction.predicted_value,
                'post_1h_glucose': prediction.post_1h_glucose,
                'post_2h_glucose': prediction.post_2h_glucose,
                'risk_level': prediction.risk_level,
                'confidence': prediction.confidence,
                'advice': prediction.advice,
                'model_mode': prediction.model_mode,
                'log_id': prediction.id,
            }
        })
