from django.contrib import admin
from .models import ChatSession, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('role', 'content', 'created_at')
    can_delete = False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'locale', 'message_count', 'started_at', 'ended_at')
    list_filter = ('locale',)
    search_fields = ('user__email',)
    ordering = ('-started_at',)
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'content_preview', 'created_at')
    list_filter = ('role',)
    search_fields = ('session__user__email', 'content')
    ordering = ('-created_at',)

    def content_preview(self, obj):
        return obj.content[:80]
    content_preview.short_description = '내용 미리보기'
