from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'nickname', 'provider', 'is_active', 'date_joined')
    list_filter = ('provider', 'is_active', 'is_staff')
    search_fields = ('email', 'nickname')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('개인 정보', {'fields': ('nickname', 'provider', 'provider_id')}),
        ('권한', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('중요한 날짜', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'due_date', 'pregnancy_week', 'is_profile_completed', 'weight')
    list_filter = ('is_profile_completed',)
    search_fields = ('user__email', 'user__nickname')
    readonly_fields = ('pregnancy_week', 'created_at', 'updated_at')
