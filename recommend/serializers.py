from rest_framework import serializers
from .models import RecommendLog


class RecommendRequestSerializer(serializers.Serializer):
    meal_type = serializers.ChoiceField(choices=['breakfast', 'lunch', 'dinner', 'snack'])
    context = serializers.DictField(required=False, default=dict)


class RecommendFeedbackSerializer(serializers.Serializer):
    user_rating = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    is_applied = serializers.BooleanField(required=False)


class RecommendLogListSerializer(serializers.ModelSerializer):
    recommend_id = serializers.IntegerField(source='id', read_only=True)
    result_summary = serializers.SerializerMethodField()

    class Meta:
        model = RecommendLog
        fields = ['recommend_id', 'result_summary', 'user_rating', 'is_applied', 'created_at']

    def get_result_summary(self, obj):
        result = obj.result or {}
        menu = result.get('menu', [])
        main = menu[0]['food_name'] if menu else ''
        return {
            'main': main,
            'total_kcal': result.get('total_kcal', 0),
        }


class RecommendLogDetailSerializer(serializers.ModelSerializer):
    recommend_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = RecommendLog
        fields = ['recommend_id', 'meal_type', 'context', 'result', 'reason', 'user_rating', 'is_applied', 'created_at']
