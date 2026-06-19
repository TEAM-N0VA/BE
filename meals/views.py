import uuid
import requests
from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import FoodInfo, MealLog, MealItem
from .serializers import (
    FoodInfoSerializer, FoodInfoListSerializer, FoodInfoCreateSerializer,
    MealLogCreateSerializer, MealLogUpdateSerializer,
    MealLogListSerializer, MealLogDetailSerializer,
    MealItemSimpleSerializer,
)


class UploadUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        filename = request.data.get('filename', '')
        content_type = request.data.get('content_type', 'image/jpeg')

        if not filename:
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': 'filename은 필수입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Try to generate S3 presigned URL if AWS is configured
        aws_key = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
        aws_bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')

        if aws_key and aws_bucket:
            try:
                import boto3
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME,
                )
                unique_key = f"meals/{uuid.uuid4()}/{filename}"
                upload_url = s3.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': aws_bucket,
                        'Key': unique_key,
                        'ContentType': content_type,
                    },
                    ExpiresIn=300,
                )
                img_url = f"https://{aws_bucket}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{unique_key}"
                return Response({
                    'code': 'OK',
                    'data': {
                        'upload_url': upload_url,
                        'img_url': img_url,
                        'expires_in': 300,
                    }
                })
            except Exception:
                pass

        # Stub response when AWS is not configured
        unique_key = f"meals/{uuid.uuid4()}/{filename}"
        stub_img_url = f"https://mealdang-stub.example.com/{unique_key}"
        stub_upload_url = f"https://mealdang-stub.example.com/upload/{unique_key}?stub=true"

        return Response({
            'code': 'OK',
            'data': {
                'upload_url': stub_upload_url,
                'img_url': stub_img_url,
                'expires_in': 300,
            }
        })


class AnalyzeImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        img_url = request.data.get('img_url')
        if not img_url:
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': 'img_url은 필수입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ai_server_url = getattr(settings, 'AI_SERVER_URL', '')
        if not ai_server_url:
            return Response(
                {'code': 'AI_SERVER_NOT_CONFIGURED', 'message': 'AI 서버가 설정되지 않았습니다.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        try:
            resp = requests.post(
                f"{ai_server_url}/analyze-image",
                json={'img_url': img_url},
                timeout=30,
            )
            resp.raise_for_status()
            ai_data = resp.json()
            return Response({'code': 'OK', 'data': ai_data})
        except requests.RequestException as e:
            return Response(
                {'code': 'AI_SERVER_ERROR', 'message': f'AI 서버와 통신 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class FoodSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 20))

        qs = FoodInfo.objects.all()
        if query:
            qs = qs.filter(
                Q(food_name__icontains=query)
            )

        total = qs.count()
        offset = (page - 1) * size
        items = qs[offset:offset + size]

        serializer = FoodInfoListSerializer(items, many=True)
        return Response({
            'code': 'OK',
            'data': {
                'items': serializer.data,
                'total': total,
                'page': page,
                'size': size,
            }
        })


class FoodDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, food_id):
        try:
            food = FoodInfo.objects.get(id=food_id)
        except FoodInfo.DoesNotExist:
            return Response(
                {'code': 'NOT_FOUND', 'message': '음식 정보를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = FoodInfoSerializer(food)
        return Response({'code': 'OK', 'data': serializer.data})


class FoodCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FoodInfoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        food = serializer.save(is_user_added=True, added_by=request.user)
        return Response({
            'code': 'OK',
            'data': {
                'food_id': food.id,
                'is_user_added': food.is_user_added,
            }
        }, status=status.HTTP_201_CREATED)


class MealLogListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils.dateparse import parse_date
        from datetime import datetime, time
        from django.utils import timezone

        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 20))

        qs = MealLog.objects.filter(user=request.user).prefetch_related('items')

        if from_date:
            dt = parse_date(from_date)
            if dt:
                qs = qs.filter(eaten_at__date__gte=dt)

        if to_date:
            dt = parse_date(to_date)
            if dt:
                qs = qs.filter(eaten_at__date__lte=dt)

        total = qs.count()
        offset = (page - 1) * size
        items = qs[offset:offset + size]

        serializer = MealLogListSerializer(items, many=True)
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
        serializer = MealLogCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        meal_log = MealLog.objects.create(
            user=request.user,
            meal_type=data['meal_type'],
            eaten_at=data['eaten_at'],
            img_url=data.get('img_url', ''),
            restaurant_id=data.get('restaurant_id'),
            nausea_level=data.get('nausea_level'),
            user_rating=data.get('user_rating'),
        )

        items_created = []
        for item_data in data.get('items', []):
            try:
                food = FoodInfo.objects.get(id=item_data['food_id'])
            except FoodInfo.DoesNotExist:
                meal_log.delete()
                return Response(
                    {'code': 'NOT_FOUND', 'message': f"음식 ID {item_data['food_id']}를 찾을 수 없습니다."},
                    status=status.HTTP_404_NOT_FOUND
                )

            meal_item = MealItem(
                meal_log=meal_log,
                food_info=food,
                recorded_name=item_data['recorded_name'],
                predicted_name=item_data.get('predicted_name', ''),
                amount_g=item_data['amount_g'],
                is_user_modified=item_data.get('is_user_modified', False),
                yolo_confidence=item_data.get('yolo_confidence'),
                bbox=item_data.get('bbox'),
            )
            meal_item.calculate_nutrition()
            meal_item.save()
            items_created.append(meal_item)

        meal_log.recalculate_totals()

        return Response({
            'code': 'OK',
            'data': {
                'id': meal_log.id,
                'meal_type': meal_log.meal_type,
                'eaten_at': meal_log.eaten_at.isoformat(),
                'total_kcal': meal_log.total_kcal,
                'total_carbs': meal_log.total_carbs,
                'items': MealItemSimpleSerializer(items_created, many=True).data,
            }
        }, status=status.HTTP_201_CREATED)


class MealLogDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_meal_log(self, request, meal_id):
        try:
            return MealLog.objects.get(id=meal_id, user=request.user)
        except MealLog.DoesNotExist:
            return None

    def get(self, request, meal_id):
        meal_log = self._get_meal_log(request, meal_id)
        if not meal_log:
            return Response(
                {'code': 'NOT_FOUND', 'message': '식사 기록을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = MealLogDetailSerializer(meal_log)
        return Response({'code': 'OK', 'data': serializer.data})

    def put(self, request, meal_id):
        meal_log = self._get_meal_log(request, meal_id)
        if not meal_log:
            return Response(
                {'code': 'NOT_FOUND', 'message': '식사 기록을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MealLogUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        if 'meal_type' in data:
            meal_log.meal_type = data['meal_type']
        if 'eaten_at' in data:
            meal_log.eaten_at = data['eaten_at']
        meal_log.save()

        if 'items' in data:
            meal_log.items.all().delete()
            for item_data in data['items']:
                try:
                    food = FoodInfo.objects.get(id=item_data['food_id'])
                except FoodInfo.DoesNotExist:
                    return Response(
                        {'code': 'NOT_FOUND', 'message': f"음식 ID {item_data['food_id']}를 찾을 수 없습니다."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                meal_item = MealItem(
                    meal_log=meal_log,
                    food_info=food,
                    recorded_name=item_data['recorded_name'],
                    amount_g=item_data['amount_g'],
                    is_user_modified=item_data.get('is_user_modified', False),
                )
                meal_item.calculate_nutrition()
                meal_item.save()
            meal_log.recalculate_totals()

        response_serializer = MealLogDetailSerializer(meal_log)
        return Response({'code': 'OK', 'data': response_serializer.data})

    def delete(self, request, meal_id):
        meal_log = self._get_meal_log(request, meal_id)
        if not meal_log:
            return Response(
                {'code': 'NOT_FOUND', 'message': '식사 기록을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
        meal_log.delete()
        return Response({'code': 'OK', 'message': '식사 기록이 삭제되었습니다.'})
