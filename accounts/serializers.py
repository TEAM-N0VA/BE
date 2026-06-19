from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserProfile


class RegisterSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=['email', 'kakao', 'google'], default='email')
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    nickname = serializers.CharField(max_length=50)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            nickname=validated_data['nickname'],
            provider=validated_data.get('provider', 'email'),
        )
        UserProfile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    Id = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['Id'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError("이메일 또는 비밀번호가 올바르지 않습니다.")
        if not user.is_active:
            raise serializers.ValidationError("비활성화된 계정입니다.")
        attrs['user'] = user
        return attrs


class SocialLoginSerializer(serializers.Serializer):
    provider_token = serializers.CharField()
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True)


class TokenRefreshInputSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    nickname = serializers.CharField(source='user.nickname', read_only=True)
    pregnancy_week = serializers.IntegerField(read_only=True)
    health_notes = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'email', 'nickname', 'due_date', 'pregnancy_week',
            'dietary_restrictions', 'flavor_preferences',
            'target_carb_per_meal', 'target_calories', 'target_bloodsugar',
            'health_notes',
        ]

    def get_health_notes(self, obj):
        return {
            'nausea_level': obj.nausea_level,
            'weight': obj.weight,
        }


class UserProfileUpdateSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=50, required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
    dietary_restrictions = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    flavor_preferences = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    target_carb_per_meal = serializers.FloatField(required=False, allow_null=True)
    target_calories = serializers.FloatField(required=False, allow_null=True)
    target_bloodsugar = serializers.FloatField(required=False, allow_null=True)
    health_notes = serializers.DictField(required=False)

    def update(self, instance, validated_data):
        user = instance.user

        if 'nickname' in validated_data:
            user.nickname = validated_data['nickname']
            user.save(update_fields=['nickname'])

        profile_fields = [
            'due_date', 'dietary_restrictions', 'flavor_preferences',
            'target_carb_per_meal', 'target_calories', 'target_bloodsugar',
        ]
        for field in profile_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        health_notes = validated_data.get('health_notes', {})
        if 'nausea_level' in health_notes:
            instance.nausea_level = health_notes['nausea_level']
        if 'weight' in health_notes:
            instance.weight = health_notes['weight']

        # Mark profile as completed if due_date is set
        if instance.due_date:
            instance.is_profile_completed = True

        instance.save()
        return instance
