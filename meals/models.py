from django.db import models
from django.conf import settings


class FoodInfo(models.Model):
    """Food database entry with nutritional information."""
    food_name = models.CharField(max_length=200)
    kcal_per_100 = models.FloatField()
    carbs_per_100 = models.FloatField()
    protein_per_100 = models.FloatField()
    fat_per_100 = models.FloatField()
    fiber_per_100 = models.FloatField(default=0)
    sugar_per_100 = models.FloatField(default=0)
    sodium_per_100 = models.FloatField(default=0)
    gi_index = models.IntegerField(null=True, blank=True)
    serving_size = models.FloatField(default=100)
    is_user_added = models.BooleanField(default=False)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='added_foods'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'food_info'

    def __str__(self):
        return self.food_name


class MealLog(models.Model):
    """A meal log entry for a user."""
    MEAL_TYPE_CHOICES = [
        ('breakfast', '아침'),
        ('lunch', '점심'),
        ('dinner', '저녁'),
        ('snack', '간식'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meal_logs'
    )
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    eaten_at = models.DateTimeField()
    img_url = models.TextField(blank=True)
    restaurant_id = models.BigIntegerField(null=True, blank=True)
    nausea_level = models.IntegerField(null=True, blank=True)
    user_rating = models.IntegerField(null=True, blank=True)
    total_kcal = models.FloatField(default=0)
    total_carbs = models.FloatField(default=0)
    total_protein = models.FloatField(default=0)
    total_fat = models.FloatField(default=0)
    predicted_glucose = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meal_logs'
        ordering = ['-eaten_at']

    def __str__(self):
        return f"{self.user.email} - {self.meal_type} - {self.eaten_at.date()}"

    def recalculate_totals(self):
        """Recalculate totals from meal items."""
        items = self.items.all()
        self.total_kcal = sum(item.kcal for item in items)
        self.total_carbs = sum(item.carbs for item in items)
        self.total_protein = sum(item.protein for item in items)
        self.total_fat = sum(item.fat for item in items)
        self.save(update_fields=['total_kcal', 'total_carbs', 'total_protein', 'total_fat'])


class MealItem(models.Model):
    """Individual food item within a meal log."""
    meal_log = models.ForeignKey(
        MealLog,
        on_delete=models.CASCADE,
        related_name='items'
    )
    food_info = models.ForeignKey(
        FoodInfo,
        on_delete=models.SET_NULL,
        null=True,
        related_name='meal_items'
    )
    recorded_name = models.CharField(max_length=200)
    predicted_name = models.CharField(max_length=200, blank=True)
    amount_g = models.FloatField()
    is_user_modified = models.BooleanField(default=False)
    yolo_confidence = models.FloatField(null=True, blank=True)
    bbox = models.JSONField(null=True, blank=True)
    kcal = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    protein = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    sugar = models.FloatField(default=0)

    class Meta:
        db_table = 'meal_items'

    def __str__(self):
        return f"{self.recorded_name} ({self.amount_g}g)"

    def calculate_nutrition(self):
        """Calculate nutrition values based on food_info and amount."""
        if self.food_info and self.amount_g:
            ratio = self.amount_g / 100.0
            self.kcal = round(self.food_info.kcal_per_100 * ratio, 2)
            self.carbs = round(self.food_info.carbs_per_100 * ratio, 2)
            self.protein = round(self.food_info.protein_per_100 * ratio, 2)
            self.fat = round(self.food_info.fat_per_100 * ratio, 2)
            self.sugar = round(self.food_info.sugar_per_100 * ratio, 2)
