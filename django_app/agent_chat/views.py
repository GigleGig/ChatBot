"""
Agent Chat API Views
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import asyncio
import uuid

from .models import Conversation, Message, AgentSession
from .serializers import ConversationSerializer, MessageSerializer, AgentSessionSerializer
from knowledge_base.services import AgentService, KnowledgeBaseService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_conversation(request):
    """Start a new conversation with the agent."""
    conversation = Conversation.objects.create(
        user=request.user,
        title=request.data.get('title', 'New Conversation')
    )
    
    # Create agent session
    agent_session = AgentSession.objects.create(
        user=request.user,
        conversation=conversation
    )
    
    return Response({
        'conversation_id': str(conversation.id),
        'session_id': str(agent_session.id),
        'title': conversation.title
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, conversation_id):
    """Send a message to the agent and get response."""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    
    user_message = request.data.get('message', '')
    use_tools = request.data.get('use_tools', True)
    workflow = request.data.get('workflow')
    
    if not user_message:
        return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Save user message
    user_msg = Message.objects.create(
        conversation=conversation,
        role='user',
        content=user_message
    )
    
    try:
        # Process with agent
        agent_service = AgentService()
        
        # Convert to async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                agent_service.process_message(
                    user_message,
                    conversation_id=str(conversation.id),
                    use_tools=use_tools,
                    workflow=workflow
                )
            )
        finally:
            loop.close()
        
        if result['success']:
            # Save agent response
            agent_msg = Message.objects.create(
                conversation=conversation,
                role='assistant',
                content=result.get('response', ''),
                tools_used=result.get('tools_used', []),
                execution_time=result.get('execution_time', 0),
                metadata=result.get('metadata', {})
            )
            
            return Response({
                'success': True,
                'response': result.get('response', ''),
                'tools_used': result.get('tools_used', []),
                'execution_time': result.get('execution_time', 0),
                'message_id': str(agent_msg.id)
            })
        else:
            # Save error message
            error_msg = Message.objects.create(
                conversation=conversation,
                role='error',
                content=result.get('error', 'Unknown error'),
                metadata=result
            )
            
            return Response({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'message_id': str(error_msg.id)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        # Save error message
        error_msg = Message.objects.create(
            conversation=conversation,
            role='error',
            content=str(e)
        )
        
        return Response({
            'success': False,
            'error': str(e),
            'message_id': str(error_msg.id)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_history(request, conversation_id):
    """Get conversation history."""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    messages = conversation.messages.all()
    
    serializer = MessageSerializer(messages, many=True)
    return Response({
        'conversation_id': str(conversation.id),
        'title': conversation.title,
        'messages': serializer.data,
        'message_count': messages.count()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_conversations(request):
    """List user's conversations."""
    conversations = Conversation.objects.filter(user=request.user, is_active=True)
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """Delete a conversation."""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    conversation.is_active = False
    conversation.save()
    
    return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_agent_tools(request):
    """Get available agent tools."""
    try:
        agent_service = AgentService()
        tools = agent_service.get_available_tools()
        workflows = agent_service.get_available_workflows()
        
        return Response({
            'tools': tools,
            'workflows': workflows
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_agent_status(request):
    """Get agent status and statistics."""
    try:
        agent_service = AgentService()
        status_info = agent_service.get_agent_status()
        
        return Response(status_info)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
