from django.contrib import admin
from .models import BloodSugarLog, BloodSugarPrediction, FoodSensitivity


@admin.register(BloodSugarLog)
class BloodSugarLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'value', 'record_type', 'risk_level', 'measured_at', 'created_at')
    list_filter = ('record_type', 'risk_level')
    search_fields = ('user__email',)
    ordering = ('-measured_at',)
    readonly_fields = ('risk_level', 'created_at', 'updated_at')


@admin.register(BloodSugarPrediction)
class BloodSugarPredictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'predicted_value', 'risk_level', 'confidence', 'model_mode', 'created_at')
    list_filter = ('risk_level', 'model_mode')
    search_fields = ('user__email',)
    ordering = ('-created_at',)


@admin.register(FoodSensitivity)
class FoodSensitivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'food_info', 'avg_spike', 'sample_count', 'updated_at')
    search_fields = ('user__email', 'food_info__food_name')
    ordering = ('-avg_spike',)
