from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, LogoutView, WithdrawView, ProfileView, HealthLogView

urlpatterns = [
    # 인증
    path('register/', RegisterView.as_view()),       # 회원가입
    path('login/', LoginView.as_view()),             # 로그인
    path('logout/', LogoutView.as_view()),           # 로그아웃
    path('token/refresh/', TokenRefreshView.as_view()),  # 토큰 갱신
    path('withdraw/', WithdrawView.as_view()),       # 회원탈퇴

    # 프로필
    path('profile/', ProfileView.as_view()),         # 프로필 조회/수정
    path('profile/health/', HealthLogView.as_view()), # 건강 기록
]