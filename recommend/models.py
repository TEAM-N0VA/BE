from django.db import models
from django.conf import settings


class RecommendLog(models.Model):
    """Stores AI-generated meal recommendations."""
    MEAL_TYPE_CHOICES = [
        ('breakfast', '아침'),
        ('lunch', '점심'),
        ('dinner', '저녁'),
        ('snack', '간식'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommend_logs'
    )
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    context = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    reason = models.TextField(blank=True)
    user_rating = models.IntegerField(null=True, blank=True)
    is_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recommend_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.meal_type} ({self.created_at.date()})"
