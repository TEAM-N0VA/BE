from django.contrib import admin
from .models import RecommendLog


@admin.register(RecommendLog)
class RecommendLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'meal_type', 'user_rating', 'is_applied', 'created_at')
    list_filter = ('meal_type', 'is_applied')
    search_fields = ('user__email',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
