"""
URLs for Agent Chat app
"""
from django.urls import path
from . import views

app_name = 'agent_chat'

urlpatterns = [
    path('conversations/', views.list_conversations, name='list_conversations'),
    path('conversations/start/', views.start_conversation, name='start_conversation'),
    path('conversations/<uuid:conversation_id>/', views.get_conversation_history, name='conversation_history'),
    path('conversations/<uuid:conversation_id>/message/', views.send_message, name='send_message'),
    path('conversations/<uuid:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('tools/', views.get_agent_tools, name='agent_tools'),
    path('status/', views.get_agent_status, name='agent_status'),
]