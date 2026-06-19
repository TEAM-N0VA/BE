from rest_framework import serializers
from .models import FoodInfo, MealLog, MealItem


class FoodInfoSerializer(serializers.ModelSerializer):
    food_id = serializers.IntegerField(source='id', read_only=True)
    nutrition_per_100 = serializers.SerializerMethodField()

    class Meta:
        model = FoodInfo
        fields = [
            'food_id', 'food_name', 'kcal_per_100', 'nutrition_per_100',
            'gi_index', 'serving_size', 'is_user_added',
        ]

    def get_nutrition_per_100(self, obj):
        return {
            'carbs': obj.carbs_per_100,
            'protein': obj.protein_per_100,
            'fat': obj.fat_per_100,
            'fiber': obj.fiber_per_100,
            'sugar': obj.sugar_per_100,
            'sodium': obj.sodium_per_100,
        }


class FoodInfoListSerializer(serializers.ModelSerializer):
    food_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = FoodInfo
        fields = ['food_id', 'food_name', 'kcal_per_100', 'carbs_per_100', 'gi_index', 'is_user_added']


class FoodInfoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodInfo
        fields = [
            'food_name', 'kcal_per_100', 'carbs_per_100', 'protein_per_100',
            'fat_per_100', 'fiber_per_100', 'sugar_per_100', 'sodium_per_100',
            'gi_index', 'serving_size',
        ]


class MealItemInputSerializer(serializers.Serializer):
    food_id = serializers.IntegerField()
    recorded_name = serializers.CharField(max_length=200)
    predicted_name = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')
    amount_g = serializers.FloatField(min_value=0)
    is_user_modified = serializers.BooleanField(default=False)
    yolo_confidence = serializers.FloatField(required=False, allow_null=True)
    bbox = serializers.DictField(required=False, allow_null=True)


class MealItemSerializer(serializers.ModelSerializer):
    food_id = serializers.IntegerField(source='food_info.id', read_only=True)
    nutrition = serializers.SerializerMethodField()

    class Meta:
        model = MealItem
        fields = [
            'id', 'food_id', 'recorded_name', 'predicted_name',
            'amount_g', 'is_user_modified', 'yolo_confidence', 'bbox',
            'nutrition',
        ]

    def get_nutrition(self, obj):
        return {
            'kcal': obj.kcal,
            'carbs': obj.carbs,
            'protein': obj.protein,
            'fat': obj.fat,
            'sugar': obj.sugar,
        }


class MealItemSimpleSerializer(serializers.ModelSerializer):
    food_id = serializers.IntegerField(source='food_info.id', read_only=True)

    class Meta:
        model = MealItem
        fields = ['id', 'food_id', 'recorded_name', 'amount_g', 'kcal']


class MealLogCreateSerializer(serializers.Serializer):
    meal_type = serializers.ChoiceField(choices=['breakfast', 'lunch', 'dinner', 'snack'])
    eaten_at = serializers.DateTimeField()
    img_url = serializers.CharField(required=False, allow_blank=True, default='')
    restaurant_id = serializers.IntegerField(required=False, allow_null=True)
    nausea_level = serializers.IntegerField(required=False, allow_null=True)
    user_rating = serializers.IntegerField(required=False, allow_null=True)
    items = MealItemInputSerializer(many=True)


class MealLogUpdateSerializer(serializers.Serializer):
    meal_type = serializers.ChoiceField(choices=['breakfast', 'lunch', 'dinner', 'snack'], required=False)
    eaten_at = serializers.DateTimeField(required=False)
    items = MealItemInputSerializer(many=True, required=False)


class MealLogListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = MealLog
        fields = [
            'id', 'meal_type', 'eaten_at', 'total_kcal', 'total_carbs',
            'img_url', 'restaurant_id', 'items_count', 'predicted_glucose',
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class MealLogDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    linked_blood_sugar = serializers.SerializerMethodField()
    predicted_blood_sugar = serializers.SerializerMethodField()

    class Meta:
        model = MealLog
        fields = [
            'id', 'meal_type', 'eaten_at', 'img_url', 'restaurant_id',
            'nausea_level', 'user_rating', 'total_kcal', 'total_carbs',
            'items', 'linked_blood_sugar', 'predicted_blood_sugar',
        ]

    def get_items(self, obj):
        return MealItemSerializer(obj.items.all(), many=True).data

    def get_linked_blood_sugar(self, obj):
        bs_logs = obj.blood_sugar_logs.all()
        return [
            {'id': bs.id, 'value': bs.value, 'record_type': bs.record_type}
            for bs in bs_logs
        ]

    def get_predicted_blood_sugar(self, obj):
        prediction = obj.predictions.first()
        if prediction:
            return {
                'predicted_value': prediction.predicted_value,
                'risk_level': prediction.risk_level,
            }
        return None
