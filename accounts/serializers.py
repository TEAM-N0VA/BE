from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, HealthLog
''' DB 데이터 ↔ JSON 변환'''
User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """회원가입용"""
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password2', 'nickname'
        ]

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data['username'] = validated_data['email']  # username 자동 설정
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)  # 프로필 자동 생성
        return user


class UserSerializer(serializers.ModelSerializer):
    """유저 정보 응답용"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'nickname', 'login_type', 'created_at'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """프로필 조회/수정용"""
    class Meta:
        model = UserProfile
        fields = [
            'due_date', 'dietary_restrictions', 'flavor_preferences',
            'target_carb_per_meal', 'target_calories', 'target_bloodsugar',
            'updated_at'
        ]


class HealthLogSerializer(serializers.ModelSerializer):
    """건강 기록용"""
    class Meta:
        model = HealthLog
        fields = [
            'id', 'nausea_level', 'avg_blood_sugar', 'weight', 'recorded_at'
        ]