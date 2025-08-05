from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Conversation(models.Model):
    """Model to track agent conversations and chat sessions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.id} - {self.user.username}"
    
    @property
    def message_count(self):
        return self.messages.count()


class Message(models.Model):
    """Individual messages in a conversation."""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    tools_used = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    execution_time = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AgentSession(models.Model):
    """Track agent sessions and their state."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_sessions')
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE, related_name='agent_session')
    memory_state = models.JSONField(default=dict, blank=True)
    tool_preferences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Agent Session {self.id} - {self.user.username}"
