import math
import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Restaurant, RestaurantScore, RestaurantFeedback
from .serializers import (
    RestaurantDetailSerializer,
    RestaurantFeedbackCreateSerializer,
)


def calculate_distance_m(lat1, lng1, lat2, lng2):
    """Calculate distance in meters between two coordinates using Haversine formula."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def calculate_total_score(base_score, personal_score, distance_m):
    """Calculate weighted total score for a restaurant."""
    distance_score = max(0, 100 - distance_m / 10)
    return 0.4 * base_score + 0.3 * personal_score + 0.3 * distance_score


class RestaurantListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = int(request.query_params.get('radius', 500))
        category = request.query_params.get('category', '')
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 20))

        if not lat or not lng:
            return Response(
                {'code': 'MISSING_PARAMS', 'message': 'lat, lng 파라미터가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response(
                {'code': 'INVALID_PARAMS', 'message': '유효하지 않은 좌표입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        kakao_api_key = getattr(settings, 'KAKAO_REST_API_KEY', '')
        kakao_results = []

        if kakao_api_key:
            try:
                query = f"{category} 음식점" if category else "음식점"
                resp = requests.get(
                    'https://dapi.kakao.com/v2/local/search/keyword.json',
                    headers={'Authorization': f'KakaoAK {kakao_api_key}'},
                    params={
                        'query': query,
                        'x': lng,
                        'y': lat,
                        'radius': radius,
                        'size': 15,
                        'category_group_code': 'FD6',
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                kakao_data = resp.json()
                kakao_results = kakao_data.get('documents', [])
            except requests.RequestException:
                pass

        # Upsert restaurants from Kakao results
        restaurants_with_score = []
        user = request.user

        for doc in kakao_results:
            kakao_place_id = str(doc.get('id', ''))
            restaurant, _ = Restaurant.objects.get_or_create(
                kakao_place_id=kakao_place_id,
                defaults={
                    'name': doc.get('place_name', ''),
                    'category': doc.get('category_name', ''),
                    'address': doc.get('road_address_name') or doc.get('address_name', ''),
                    'phone': doc.get('phone', ''),
                    'lat': float(doc.get('y', lat)),
                    'lng': float(doc.get('x', lng)),
                    'base_score': 50,
                }
            )

            dist = calculate_distance_m(lat, lng, restaurant.lat, restaurant.lng)
            score_obj = RestaurantScore.objects.filter(user=user, restaurant=restaurant).first()
            personal_score = score_obj.personal_score if score_obj else 50
            total_score = calculate_total_score(restaurant.base_score, personal_score, dist)

            restaurants_with_score.append({
                'restaurant_id': restaurant.id,
                'kakao_place_id': restaurant.kakao_place_id,
                'name': restaurant.name,
                'category': restaurant.category,
                'address': restaurant.address,
                'lat': restaurant.lat,
                'lng': restaurant.lng,
                'distance_m': round(dist, 1),
                'total_score': round(total_score, 2),
                'visit_count': score_obj.visit_count if score_obj else 0,
                'last_actual_glucose': score_obj.last_actual_glucose if score_obj else None,
                'is_personalized': score_obj is not None,
            })

        # Sort by total_score descending
        restaurants_with_score.sort(key=lambda x: x['total_score'], reverse=True)

        total = len(restaurants_with_score)
        offset = (page - 1) * size
        items = restaurants_with_score[offset:offset + size]

        return Response({
            'code': 'OK',
            'data': {
                'items': items,
                'total': total,
                'page': page,
                'size': size,
            }
        })


class RestaurantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, restaurant_id):
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response(
                {'code': 'NOT_FOUND', 'message': '음식점을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Compute distance_score if lat/lng are provided as query params
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        distance_score = 50
        if lat and lng:
            try:
                dist = calculate_distance_m(float(lat), float(lng), restaurant.lat, restaurant.lng)
                distance_score = max(0, 100 - dist / 10)
            except (ValueError, TypeError):
                pass

        serializer = RestaurantDetailSerializer(
            restaurant,
            context={'user': request.user, 'distance_score': distance_score}
        )
        return Response({'code': 'OK', 'data': serializer.data})


class RestaurantFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, restaurant_id):
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response(
                {'code': 'NOT_FOUND', 'message': '음식점을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RestaurantFeedbackCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        user = request.user

        meal_log = None
        meal_log_id = data.get('meal_log_id')
        if meal_log_id:
            from meals.models import MealLog
            try:
                meal_log = MealLog.objects.get(id=meal_log_id, user=user)
            except MealLog.DoesNotExist:
                pass

        # Create feedback
        RestaurantFeedback.objects.create(
            user=user,
            restaurant=restaurant,
            actual_glucose=data.get('actual_glucose'),
            meal_log=meal_log,
            user_rating=data.get('user_rating'),
            memo=data.get('memo', ''),
        )

        # Update restaurant score with EMA
        score_obj, created = RestaurantScore.objects.get_or_create(
            user=user,
            restaurant=restaurant,
            defaults={'personal_score': 50, 'total_score': 50, 'visit_count': 0}
        )
        score_obj.visit_count += 1

        actual_glucose = data.get('actual_glucose')
        if actual_glucose is not None:
            # Convert glucose to a score (lower glucose = higher score)
            # Target range: <140 is good, scale 0-100
            glucose_score = max(0, min(100, 100 - (actual_glucose - 140) * 2)) if actual_glucose > 140 else 100

            alpha = 0.3
            if created or score_obj.last_actual_glucose is None:
                score_obj.personal_score = glucose_score
            else:
                score_obj.personal_score = alpha * glucose_score + (1 - alpha) * score_obj.personal_score

            score_obj.last_actual_glucose = actual_glucose
            score_obj.ema_updated_at = timezone.now()

        # Recompute total_score
        score_obj.total_score = round(
            0.4 * restaurant.base_score + 0.3 * score_obj.personal_score + 0.3 * 50, 2
        )
        score_obj.save()

        return Response({
            'code': 'OK',
            'data': {
                'restaurant_id': restaurant.id,
                'updated_total_score': score_obj.total_score,
                'visit_count': score_obj.visit_count,
                'ema_alpha': 0.3,
            }
        }, status=status.HTTP_201_CREATED)
