import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User, UserProfile
from .serializers import (
    RegisterSerializer, LoginSerializer, SocialLoginSerializer,
    TokenRefreshInputSerializer, LogoutSerializer,
    UserProfileSerializer, UserProfileUpdateSerializer,
)


def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        profile, _ = UserProfile.objects.get_or_create(user=user)

        return Response({
            'code': 'OK',
            'message': '회원가입이 완료되었습니다.',
            'data': {
                'user_id': user.id,
                'email': user.email,
                'nickname': user.nickname,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'is_profile_completed': profile.is_profile_completed,
            }
        }, status=status.HTTP_201_CREATED)


class SocialLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, provider):
        if provider not in ('kakao', 'google'):
            return Response(
                {'code': 'INVALID_PROVIDER', 'message': '지원하지 않는 소셜 로그인입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SocialLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        provider_token = serializer.validated_data['provider_token']
        nickname = serializer.validated_data.get('nickname', '')

        social_user_info = self._verify_social_token(provider, provider_token)
        if not social_user_info:
            return Response(
                {'code': 'INVALID_TOKEN', 'message': '소셜 토큰이 유효하지 않습니다.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        email = social_user_info.get('email')
        provider_id = str(social_user_info.get('id', ''))
        social_nickname = social_user_info.get('nickname', '')

        is_new_user = False
        user = User.objects.filter(provider=provider, provider_id=provider_id).first()

        if not user:
            user = User.objects.filter(email=email).first()
            if user:
                user.provider = provider
                user.provider_id = provider_id
                user.save(update_fields=['provider', 'provider_id'])
            else:
                is_new_user = True
                final_nickname = social_nickname or nickname or email.split('@')[0]
                user = User.objects.create_user(
                    email=email,
                    password=None,
                    nickname=final_nickname,
                    provider=provider,
                    provider_id=provider_id,
                )
                UserProfile.objects.create(user=user)

        profile, _ = UserProfile.objects.get_or_create(user=user)
        tokens = get_tokens_for_user(user)

        return Response({
            'code': 'OK',
            'data': {
                'user_id': user.id,
                'is_new_user': is_new_user,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'is_profile_completed': profile.is_profile_completed,
            }
        }, status=status.HTTP_200_OK)

    def _verify_social_token(self, provider, token):
        """Verify token with social provider and return user info dict."""
        try:
            if provider == 'kakao':
                resp = requests.get(
                    'https://kapi.kakao.com/v2/user/me',
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=10
                )
                if resp.status_code != 200:
                    return None
                data = resp.json()
                kakao_account = data.get('kakao_account', {})
                profile = kakao_account.get('profile', {})
                return {
                    'id': str(data.get('id', '')),
                    'email': kakao_account.get('email', ''),
                    'nickname': profile.get('nickname', ''),
                }
            elif provider == 'google':
                resp = requests.get(
                    'https://www.googleapis.com/oauth2/v3/userinfo',
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=10
                )
                if resp.status_code != 200:
                    return None
                data = resp.json()
                return {
                    'id': data.get('sub', ''),
                    'email': data.get('email', ''),
                    'nickname': data.get('name', ''),
                }
        except requests.RequestException:
            return None
        return None


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)

        return Response({
            'code': 'OK',
            'data': {
                'user_id': user.id,
                'nickname': user.nickname,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh_token = serializer.validated_data['refresh_token']
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {'code': 'INVALID_TOKEN', 'message': '유효하지 않은 토큰입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'code': 'OK',
            'message': '로그아웃되었습니다.'
        }, status=status.HTTP_200_OK)


class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=['is_active'])

        return Response({
            'code': 'OK',
            'message': '회원탈퇴가 완료되었습니다.'
        }, status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            old_refresh = RefreshToken(serializer.validated_data['refresh_token'])
            old_refresh.blacklist()
            user_id = old_refresh['user_id']
            user = User.objects.get(id=user_id)
            tokens = get_tokens_for_user(user)
        except TokenError:
            return Response(
                {'code': 'INVALID_TOKEN', 'message': '유효하지 않은 리프레시 토큰입니다.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except User.DoesNotExist:
            return Response(
                {'code': 'USER_NOT_FOUND', 'message': '사용자를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'code': 'OK',
            'data': {
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
            }
        }, status=status.HTTP_200_OK)


# ─── Profile / Dashboard / Report Views ───────────────────────────────────────

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response({'code': 'OK', 'data': serializer.data})

    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        updated_profile = serializer.update(profile, serializer.validated_data)
        response_serializer = UserProfileSerializer(updated_profile)
        return Response({'code': 'OK', 'data': response_serializer.data})


class DashboardTodayView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils.dateparse import parse_date
        from meals.models import MealLog
        from blood_sugar.models import BloodSugarLog
        from django.db.models import Avg, Sum
        from datetime import timedelta

        date_str = request.query_params.get('date')
        if date_str:
            target_date = parse_date(date_str)
        else:
            target_date = timezone.now().date()

        if not target_date:
            return Response(
                {'code': 'INVALID_DATE', 'message': '날짜 형식이 올바르지 않습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        meal_logs = MealLog.objects.filter(user=user, eaten_at__date=target_date)

        def get_meal_info(meal_type):
            log = meal_logs.filter(meal_type=meal_type).first()
            if log:
                return {'meal_log_id': log.id, 'total_kcal': log.total_kcal, 'is_logged': True}
            return {'meal_log_id': None, 'total_kcal': 0, 'is_logged': False}

        bs_logs = BloodSugarLog.objects.filter(user=user, measured_at__date=target_date)

        fasting = bs_logs.filter(record_type='공복').first()
        post_breakfast = bs_logs.filter(record_type='식후1시간').first()
        post_lunch = bs_logs.filter(record_type='식후1시간').last()
        latest = bs_logs.order_by('-measured_at').first()

        totals = meal_logs.aggregate(
            total_kcal=Sum('total_kcal'),
            total_carbs=Sum('total_carbs'),
            total_protein=Sum('total_protein'),
            total_fat=Sum('total_fat'),
        )

        week_ago = target_date - timedelta(days=7)
        weekly_avg = BloodSugarLog.objects.filter(
            user=user,
            measured_at__date__gte=week_ago,
            measured_at__date__lte=target_date,
        ).aggregate(avg=Avg('value'))['avg']

        next_predicted = None
        latest_meal = meal_logs.order_by('-eaten_at').first()
        if latest_meal:
            next_predicted = latest_meal.predicted_glucose

        warning = None
        if latest and latest.risk_level == '위험':
            warning = '혈당이 위험 수준입니다. 주의하세요.'

        return Response({
            'code': 'OK',
            'data': {
                'date': str(target_date),
                'meals': {
                    'breakfast': get_meal_info('breakfast'),
                    'lunch': get_meal_info('lunch'),
                    'dinner': get_meal_info('dinner'),
                },
                'blood_sugar': {
                    'fasting': fasting.value if fasting else None,
                    'post_breakfast_1h': post_breakfast.value if post_breakfast else None,
                    'post_lunch_1h': post_lunch.value if post_lunch else None,
                    'latest_risk_level': latest.risk_level if latest else None,
                },
                'today_total': {
                    'kcal': totals['total_kcal'] or 0,
                    'carbs': totals['total_carbs'] or 0,
                    'protein': totals['total_protein'] or 0,
                    'fat': totals['total_fat'] or 0,
                },
                'next_predicted_glucose': next_predicted,
                'weekly_avg_glucose': round(weekly_avg, 1) if weekly_avg else None,
                'warning': warning,
            }
        })


class ReportCalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from meals.models import MealLog
        from blood_sugar.models import BloodSugarLog
        from django.db.models import Max
        import calendar
        from datetime import date

        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if not year or not month:
            return Response(
                {'code': 'MISSING_PARAMS', 'message': 'year와 month 파라미터가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return Response(
                {'code': 'INVALID_PARAMS', 'message': '유효하지 않은 연도 또는 월입니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        _, days_in_month = calendar.monthrange(year, month)

        days_data = []
        for day in range(1, days_in_month + 1):
            current_date = date(year, month, day)

            meal_count = MealLog.objects.filter(
                user=user, eaten_at__date=current_date
            ).count()

            bs_logs = BloodSugarLog.objects.filter(
                user=user, measured_at__date=current_date
            )
            bs_count = bs_logs.count()
            max_glucose = bs_logs.aggregate(max_val=Max('value'))['max_val']

            risk_level = None
            if max_glucose:
                latest_bs = bs_logs.order_by('-measured_at').first()
                if latest_bs:
                    risk_level = latest_bs.risk_level

            days_data.append({
                'date': str(current_date),
                'meal_count': meal_count,
                'blood_sugar_count': bs_count,
                'max_glucose': max_glucose,
                'risk_level': risk_level,
            })

        return Response({
            'code': 'OK',
            'data': {
                'year': year,
                'month': month,
                'days': days_data,
            }
        })


class ReportDailyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils.dateparse import parse_date
        from meals.models import MealLog
        from blood_sugar.models import BloodSugarLog
        from django.db.models import Avg, Sum

        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {'code': 'MISSING_PARAMS', 'message': 'date 파라미터가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_date = parse_date(date_str)
        if not target_date:
            return Response(
                {'code': 'INVALID_DATE', 'message': '날짜 형식이 올바르지 않습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        meal_logs = MealLog.objects.filter(
            user=user, eaten_at__date=target_date
        ).prefetch_related('items')

        meals_data = []
        for log in meal_logs:
            meals_data.append({
                'id': log.id,
                'meal_type': log.meal_type,
                'eaten_at': log.eaten_at.isoformat(),
                'total_kcal': log.total_kcal,
                'items_count': log.items.count(),
            })

        bs_logs = BloodSugarLog.objects.filter(
            user=user, measured_at__date=target_date
        )

        bs_data = []
        for log in bs_logs:
            bs_data.append({
                'id': log.id,
                'value': log.value,
                'record_type': log.record_type,
                'measured_at': log.measured_at.isoformat(),
                'risk_level': log.risk_level,
            })

        totals = meal_logs.aggregate(
            total_kcal=Sum('total_kcal'),
            total_carbs=Sum('total_carbs'),
        )
        avg_glucose = bs_logs.aggregate(avg=Avg('value'))['avg']
        spike_events = bs_logs.filter(risk_level='위험').count()

        return Response({
            'code': 'OK',
            'data': {
                'date': str(target_date),
                'meals': meals_data,
                'blood_sugar_logs': bs_data,
                'summary': {
                    'total_kcal': totals['total_kcal'] or 0,
                    'total_carbs': totals['total_carbs'] or 0,
                    'avg_glucose': round(avg_glucose, 1) if avg_glucose else None,
                    'spike_events': spike_events,
                },
            }
        })
