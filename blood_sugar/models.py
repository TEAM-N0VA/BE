from django.db import models
from django.conf import settings


def calculate_risk_level(value, record_type):
    """Calculate blood sugar risk level based on value and record type."""
    thresholds = {
        '공복': (95, 105),
        '식전': (95, 105),
        '식후1시간': (140, 180),
        '식후2시간': (120, 150),
        '취침전': (110, 140),
    }
    low, high = thresholds.get(record_type, (140, 180))
    if value < low:
        return '안전'
    elif value < high:
        return '주의'
    return '위험'


class BloodSugarLog(models.Model):
    """Blood sugar measurement log."""
    RECORD_TYPE_CHOICES = [
        ('공복', '공복'),
        ('식전', '식전'),
        ('식후1시간', '식후1시간'),
        ('식후2시간', '식후2시간'),
        ('취침전', '취침전'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blood_sugar_logs'
    )
    value = models.FloatField()
    measured_at = models.DateTimeField()
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES)
    risk_level = models.CharField(max_length=10, blank=True)
    meal_log = models.ForeignKey(
        'meals.MealLog',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='blood_sugar_logs'
    )
    memo = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'blood_sugar_logs'
        ordering = ['-measured_at']

    def __str__(self):
        return f"{self.user.email} - {self.record_type}: {self.value} ({self.measured_at.date()})"

    def save(self, *args, **kwargs):
        # Auto-calculate risk level
        if self.value and self.record_type:
            self.risk_level = calculate_risk_level(self.value, self.record_type)
        super().save(*args, **kwargs)


class BloodSugarPrediction(models.Model):
    """AI-predicted blood sugar values for a meal."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blood_sugar_predictions'
    )
    meal_log = models.ForeignKey(
        'meals.MealLog',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='predictions'
    )
    fasting_glucose = models.FloatField(null=True, blank=True)
    predicted_value = models.FloatField()
    post_1h_glucose = models.FloatField(null=True, blank=True)
    post_2h_glucose = models.FloatField(null=True, blank=True)
    risk_level = models.CharField(max_length=10)
    confidence = models.FloatField(null=True, blank=True)
    advice = models.TextField(blank=True)
    model_mode = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blood_sugar_predictions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - predicted: {self.predicted_value} ({self.created_at.date()})"


class FoodSensitivity(models.Model):
    """Tracks user's blood sugar sensitivity to specific foods."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='food_sensitivities'
    )
    food_info = models.ForeignKey(
        'meals.FoodInfo',
        on_delete=models.CASCADE,
        related_name='sensitivities'
    )
    avg_spike = models.FloatField(default=0)
    sample_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'food_sensitivities'
        unique_together = ('user', 'food_info')

    def __str__(self):
        return f"{self.user.email} - {self.food_info.food_name}: avg_spike={self.avg_spike}"
