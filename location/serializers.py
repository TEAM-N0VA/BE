from rest_framework import serializers
from .models import Restaurant, RestaurantScore, RestaurantFeedback


class RestaurantListItemSerializer(serializers.Serializer):
    restaurant_id = serializers.IntegerField()
    kakao_place_id = serializers.CharField()
    name = serializers.CharField()
    category = serializers.CharField()
    address = serializers.CharField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    distance_m = serializers.FloatField()
    total_score = serializers.FloatField()
    visit_count = serializers.IntegerField()
    last_actual_glucose = serializers.FloatField(allow_null=True)
    is_personalized = serializers.BooleanField()


class RestaurantDetailSerializer(serializers.ModelSerializer):
    restaurant_id = serializers.IntegerField(source='id', read_only=True)
    score = serializers.SerializerMethodField()
    menu_recommendations = serializers.SerializerMethodField()
    score_explanation = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            'restaurant_id', 'name', 'category', 'address', 'phone',
            'lat', 'lng', 'score', 'menu_recommendations', 'score_explanation',
        ]

    def get_score(self, obj):
        user = self.context.get('user')
        score_obj = None
        if user:
            score_obj = RestaurantScore.objects.filter(user=user, restaurant=obj).first()

        return {
            'base_score': obj.base_score,
            'distance_score': self.context.get('distance_score', 50),
            'personal_score': score_obj.personal_score if score_obj else 50,
            'total_score': score_obj.total_score if score_obj else obj.base_score,
            'visit_count': score_obj.visit_count if score_obj else 0,
            'last_actual_glucose': score_obj.last_actual_glucose if score_obj else None,
            'ema_updated_at': score_obj.ema_updated_at.isoformat() if (score_obj and score_obj.ema_updated_at) else None,
        }

    def get_menu_recommendations(self, obj):
        # Placeholder - would integrate with AI server in production
        return []

    def get_score_explanation(self, obj):
        return f"{obj.name}의 점수는 기본 점수, 거리 점수, 개인화 점수의 가중 평균입니다."


class RestaurantFeedbackCreateSerializer(serializers.Serializer):
    actual_glucose = serializers.FloatField(required=False, allow_null=True)
    meal_log_id = serializers.IntegerField(required=False, allow_null=True)
    user_rating = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    memo = serializers.CharField(required=False, allow_blank=True, default='')
