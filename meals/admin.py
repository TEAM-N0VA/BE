from django.contrib import admin
from .models import FoodInfo, MealLog, MealItem


@admin.register(FoodInfo)
class FoodInfoAdmin(admin.ModelAdmin):
    list_display = ('food_name', 'kcal_per_100', 'carbs_per_100', 'gi_index', 'is_user_added', 'created_at')
    list_filter = ('is_user_added',)
    search_fields = ('food_name',)
    ordering = ('food_name',)


class MealItemInline(admin.TabularInline):
    model = MealItem
    extra = 0
    readonly_fields = ('kcal', 'carbs', 'protein', 'fat', 'sugar')


@admin.register(MealLog)
class MealLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'meal_type', 'eaten_at', 'total_kcal', 'total_carbs', 'created_at')
    list_filter = ('meal_type',)
    search_fields = ('user__email',)
    ordering = ('-eaten_at',)
    inlines = [MealItemInline]


@admin.register(MealItem)
class MealItemAdmin(admin.ModelAdmin):
    list_display = ('recorded_name', 'meal_log', 'amount_g', 'kcal', 'carbs')
    search_fields = ('recorded_name',)
