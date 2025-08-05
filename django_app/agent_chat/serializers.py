"""
Serializers for Agent Chat app
"""
from rest_framework import serializers
from .models import Conversation, Message, AgentSession


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    
    class Meta:
        model = Message
        fields = [
            'id', 'role', 'content', 'metadata', 'tools_used',
            'created_at', 'execution_time'
        ]
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model."""
    message_count = serializers.ReadOnlyField()
    latest_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'title', 'created_at', 'updated_at', 'is_active',
            'message_count', 'latest_message'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'message_count']
    
    def get_latest_message(self, obj):
        """Get the latest message in the conversation."""
        latest = obj.messages.order_by('-created_at').first()
        if latest:
            return {
                'role': latest.role,
                'content': latest.content[:100] + '...' if len(latest.content) > 100 else latest.content,
                'created_at': latest.created_at
            }
        return None


class AgentSessionSerializer(serializers.ModelSerializer):
    """Serializer for AgentSession model."""
    
    class Meta:
        model = AgentSession
        fields = [
            'id', 'memory_state', 'tool_preferences',
            'created_at', 'last_activity'
        ]
        read_only_fields = ['id', 'created_at', 'last_activity']