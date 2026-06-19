from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """A chatbot session for a user."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_sessions'
    )
    locale = models.CharField(max_length=10, default='ko')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-started_at']

    def __str__(self):
        return f"Session #{self.id} - {self.user.email} ({self.started_at.date()})"

    @property
    def last_message_preview(self):
        last_msg = self.messages.order_by('-created_at').first()
        if last_msg:
            return last_msg.content[:100]
        return ''

    @property
    def message_count(self):
        return self.messages.count()


class ChatMessage(models.Model):
    """A single message in a chat session."""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    rag_sources = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:50]} (Session #{self.session_id})"
