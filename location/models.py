from django.db import models
from django.conf import settings


class Restaurant(models.Model):
    """Restaurant information from Kakao Map API."""
    kakao_place_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    address = models.CharField(max_length=300)
    phone = models.CharField(max_length=50, blank=True)
    lat = models.FloatField()
    lng = models.FloatField()
    base_score = models.FloatField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurants'

    def __str__(self):
        return f"{self.name} ({self.category})"


class RestaurantScore(models.Model):
    """Per-user restaurant scoring data."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='restaurant_scores'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='user_scores'
    )
    personal_score = models.FloatField(default=50)
    total_score = models.FloatField(default=50)
    visit_count = models.IntegerField(default=0)
    last_actual_glucose = models.FloatField(null=True, blank=True)
    ema_updated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'restaurant_scores'
        unique_together = ('user', 'restaurant')

    def __str__(self):
        return f"{self.user.email} - {self.restaurant.name}: {self.total_score}"


class RestaurantFeedback(models.Model):
    """User feedback for a restaurant visit."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='restaurant_feedbacks'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    actual_glucose = models.FloatField(null=True, blank=True)
    meal_log = models.ForeignKey(
        'meals.MealLog',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='restaurant_feedbacks'
    )
    user_rating = models.IntegerField(null=True, blank=True)
    memo = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'restaurant_feedbacks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.restaurant.name} feedback"
