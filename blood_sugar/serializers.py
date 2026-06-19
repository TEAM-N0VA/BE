from rest_framework import serializers
from .models import BloodSugarLog, BloodSugarPrediction


class BloodSugarLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodSugarLog
        fields = ['id', 'value', 'measured_at', 'record_type', 'risk_level', 'meal_log', 'memo']
        read_only_fields = ['risk_level']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['meal_log_id'] = data.pop('meal_log', None)
        return data


class BloodSugarLogCreateSerializer(serializers.Serializer):
    value = serializers.FloatField(min_value=0)
    measured_at = serializers.DateTimeField()
    record_type = serializers.ChoiceField(choices=['공복', '식전', '식후1시간', '식후2시간', '취침전'])
    meal_log_id = serializers.IntegerField(required=False, allow_null=True)
    memo = serializers.CharField(required=False, allow_blank=True, default='')


class BloodSugarLogUpdateSerializer(serializers.Serializer):
    value = serializers.FloatField(min_value=0, required=False)
    measured_at = serializers.DateTimeField(required=False)
    record_type = serializers.ChoiceField(
        choices=['공복', '식전', '식후1시간', '식후2시간', '취침전'], required=False
    )
    memo = serializers.CharField(required=False, allow_blank=True)


class BloodSugarPredictionRequestSerializer(serializers.Serializer):
    fasting_glucose = serializers.FloatField(required=False, allow_null=True)
    meal_log_id = serializers.IntegerField(required=False, allow_null=True)
    planned_items = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )


class BloodSugarPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodSugarPrediction
        fields = [
            'id', 'meal_log', 'fasting_glucose', 'predicted_value',
            'post_1h_glucose', 'post_2h_glucose', 'risk_level',
            'confidence', 'advice', 'model_mode', 'created_at',
        ]
