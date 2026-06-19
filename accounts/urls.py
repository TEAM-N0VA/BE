from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, WithdrawView,
    SocialLoginView, TokenRefreshView,
)

urlpatterns = [
    path('register', RegisterView.as_view(), name='auth-register'),
    path('login', LoginView.as_view(), name='auth-login'),
    path('logout', LogoutView.as_view(), name='auth-logout'),
    path('withdraw', WithdrawView.as_view(), name='auth-withdraw'),
    path('social/<str:provider>', SocialLoginView.as_view(), name='auth-social'),
    path('token/refresh', TokenRefreshView.as_view(), name='auth-token-refresh'),
]
