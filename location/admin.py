from django.contrib import admin
from .models import Restaurant, RestaurantScore, RestaurantFeedback


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'address', 'base_score', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'address', 'kakao_place_id')
    ordering = ('name',)


@admin.register(RestaurantScore)
class RestaurantScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant', 'personal_score', 'total_score', 'visit_count', 'last_actual_glucose')
    search_fields = ('user__email', 'restaurant__name')
    ordering = ('-total_score',)


@admin.register(RestaurantFeedback)
class RestaurantFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant', 'actual_glucose', 'user_rating', 'created_at')
    search_fields = ('user__email', 'restaurant__name')
    ordering = ('-created_at',)
