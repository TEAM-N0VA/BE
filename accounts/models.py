from django.db import models

# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """users 테이블 - 기본 인증 정보"""
    email = models.EmailField(max_length=254, unique=True)
    nickname = models.CharField(max_length=50)

    # 소셜 로그인 대비
    LOGIN_TYPE_CHOICES = [
        ('email', '이메일'),
        ('kakao', '카카오'),
        ('google', '구글'),
    ]
    login_type = models.CharField(max_length=10, choices=LOGIN_TYPE_CHOICES, default='email')
    social_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nickname']

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """user_profiles 테이블 - 수정 가능성 적은 개인 정보"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    due_date = models.DateField(null=True, blank=True)
    dietary_restrictions = models.JSONField(default=list, blank=True)
    flavor_preferences = models.JSONField(default=list, blank=True)
    target_carb_per_meal = models.JSONField(default=dict, blank=True)
    target_calories = models.IntegerField(null=True, blank=True)
    target_bloodsugar = models.FloatField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}의 프로필"


class HealthLog(models.Model):
    """health_logs 테이블 - 자주 바뀌는 건강 정보"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_logs')
    nausea_level = models.IntegerField()
    avg_blood_sugar = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    recorded_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user.email} - {self.recorded_at}"