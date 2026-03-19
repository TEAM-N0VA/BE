from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, UserSerializer, UserProfileSerializer, HealthLogSerializer
from .models import HealthLog


class RegisterView(APIView):
    """회원가입 - POST /auth/register/"""
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "회원가입 성공",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """로그인 - POST /auth/login/"""
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "로그인 성공",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data
            })
        return Response(
            {"message": "이메일 또는 비밀번호가 틀렸습니다."},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    """로그아웃 - POST /auth/logout/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "로그아웃 성공"})
        except Exception:
            return Response(
                {"message": "유효하지 않은 토큰입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )


class WithdrawView(APIView):
    """회원탈퇴 - DELETE /auth/withdraw/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        request.user.delete()
        return Response({"message": "회원탈퇴 완료"})


class ProfileView(APIView):
    """프로필 조회/수정 - GET, PUT /profile/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        return Response(UserProfileSerializer(profile).data)

    def put(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "프로필 수정 성공", "profile": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HealthLogView(APIView):
    """건강 기록 - GET, POST /profile/health/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = HealthLog.objects.filter(user=request.user).order_by('-recorded_at')
        return Response(HealthLogSerializer(logs, many=True).data)

    def post(self, request):
        serializer = HealthLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"message": "건강 기록 저장 성공"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)