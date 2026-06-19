from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Custom user model using email as username."""
    username = None
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=50)
    provider = models.CharField(
        max_length=10,
        choices=[('email', 'Email'), ('kakao', 'Kakao'), ('google', 'Google')],
        default='email'
    )
    provider_id = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """Extended profile for gestational diabetes management."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    due_date = models.DateField(null=True, blank=True)
    dietary_restrictions = models.JSONField(default=list, blank=True)
    flavor_preferences = models.JSONField(default=list, blank=True)
    target_carb_per_meal = models.FloatField(null=True, blank=True)
    target_calories = models.FloatField(null=True, blank=True)
    target_bloodsugar = models.FloatField(null=True, blank=True)
    nausea_level = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    is_profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile of {self.user.email}"

    @property
    def pregnancy_week(self):
        """Calculate current pregnancy week from due_date (280 days total)."""
        if not self.due_date:
            return None
        today = timezone.now().date()
        days_until_due = (self.due_date - today).days
        days_pregnant = 280 - days_until_due
        if days_pregnant < 0:
            return 0
        week = days_pregnant // 7
        return max(0, min(week, 42))
