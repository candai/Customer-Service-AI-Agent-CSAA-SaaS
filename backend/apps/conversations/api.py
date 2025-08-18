# apps/conversations/api.py
from ninja import Query, Router, Schema
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg

from .models import Conversation, Message
from apps.agents.models import Agent
from apps.accounts.api import auth
from django.utils import timezone    

router = Router(tags=["Conversations"])

from .schemas import *
import logging
import json

logger = logging.getLogger(__name__)

# Endpoints
@router.get("/dashboard/stats", response=ConversationStatsResponse, auth=auth)
def get_dashboard_stats(request):
    """Get dashboard statistics for the fronend"""
    
    user = request.user
    organization = user.organization
    
    # Get conversation stats
    total_conversations = Conversation.objects.filter(
        agent__organization=organization
    ).count()
    
    active_conversations = Conversation.objects.filter(
        agent__organization=organization,
        status__in=['active', 'waiting']
    ).count()
    
    # Get message stats
    total_messages = Message.objects.filter(
        conversation__agent__organization=organization
    ).exclude(sender_type='system').count()
    
    # Get agent stats
    total_agents = Agent.objects.filter(
        organization=organization,
        is_active=True
    ).count()
    
    # Calculate average response time (in seconds)
    avg_response_time = Conversation.objects.filter(
        agent__organization=organization,
        first_response_time_seconds__isnull=False
    ).aggregate(
        avg=Avg('first_response_time_seconds')
    )['avg'] or 0
    
    # Mock satisfaction score for now (implement actual calculation later)
    satisfaction_score = 4.5
    
    return {
        'total_conversations': total_conversations,
        'active_conversations': active_conversations,
        'total_messages': total_messages,
        'total_agents': total_agents,
        'response_time_avg': round(avg_response_time, 2),
        'satisfaction_score': satisfaction_score,
    }

# Search Conversations
@router.get("/search", auth=auth, response=ConversationSearchResponse)
def search_conversations(request, params: ConversationSearchParams = Query(...)):
    """Advanced conversation search with filters"""
    logger.info(f"Searching conversations with params: {params}")
    try:
        user = request.auth
        
        # Base queryset
        queryset = Conversation.objects.filter(
            agent__organization=user.organization
        ).select_related('agent', 'assigned_to')
        
        # Apply filters
        
        if params.query:
            # Search in messages content and customer info
            queryset = queryset.filter(
                Q(customer_name__icontains=params.query) |
                Q(customer_phone__icontains=params.query) |
                Q(messages__content__icontains=params.query)
            ).distinct()
        
        if params.status:
            queryset = queryset.filter(status=params.status)
        
        if params.channel:
            queryset = queryset.filter(channel=params.channel)
        
        if params.agent_id:
            queryset = queryset.filter(agent_id=params.agent_id)
        
        if params.customer_phone:
            queryset = queryset.filter(customer_phone__icontains=params.customer_phone)
        
        if params.date_from:
            queryset = queryset.filter(started_at__gte=params.date_from)
        
        if params.date_to:
            queryset = queryset.filter(started_at__lte=params.date_to)
        
        if params.has_handoff is not None:
            if params.has_handoff:
                queryset = queryset.filter(handed_off_at__isnull=False)
            else:
                queryset = queryset.filter(handed_off_at__isnull=True)
        
        if params.min_messages:
            queryset = queryset.filter(message_count__gte=params.min_messages)
        
        if params.max_messages:
            queryset = queryset.filter(message_count__lte=params.max_messages)
        
        # Get total count before pagination
        total = Conversation.objects.filter(
            agent__organization=user.organization
        ).count()
        filtered = queryset.count()
        
        # Sorting
        order_prefix = '-' if params.order == 'desc' else ''
        if params.sort_by in ['last_message_at', 'started_at', 'message_count']:
            queryset = queryset.order_by(f'{order_prefix}{params.sort_by}')
        
        # Pagination
        queryset = queryset[params.offset:params.offset + params.limit]
        
        # Format response
        conversations = []
        for conv in queryset:
            # Get last message
            last_message = conv.messages.order_by('-created_at').first()
            
            conversations.append({
                'id': str(conv.id),
                'agent_id': str(conv.agent.id),
                'agent_name': conv.agent.name,
                'customer_phone': conv.customer_phone,
                'customer_name': conv.customer_name,
                'channel': conv.channel,
                'status': conv.status,
                'started_at': conv.started_at.isoformat() if conv.started_at else None,
                'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None,
                'message_count': conv.message_count,
                'handed_off_at': conv.handed_off_at.isoformat() if conv.handed_off_at else None,
                'assigned_to': conv.assigned_to.email if conv.assigned_to else None,
                'last_message': {
                    'content': last_message.content[:100] if last_message else None,
                    'sender_type': last_message.sender_type if last_message else None,
                    'created_at': last_message.created_at.isoformat() if last_message else None,
                } if last_message else None,
                'metadata': conv.metadata,
            })
        
        return {
            'conversations': conversations,
            'total': total,
            'filtered': filtered,
            'page_size': params.limit,
            'page': (params.offset // params.limit) + 1,
        }
    except Exception as e:
        logger.error(f"Error in search_conversations: {e}")
        return {
            'conversations': [],
            'total': 0,
            'filtered': 0,
            'page_size': params.limit,
            'page': 1,
        }

@router.get("/", response=List[ConversationResponse], auth=auth)
def list_conversations(
    request,
    status: Optional[str] = None,
    channel: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List conversations for the organization"""
    
    user = request.auth
    
    # Base query
    query = Conversation.objects.filter(
        agent__organization=user.organization
    ).select_related('agent')
    
    # Apply filters
    if status:
        query = query.filter(status=status)
    if channel:
        query = query.filter(channel=channel)
    if agent_id:
        query = query.filter(agent_id=agent_id)
    
    # Order and paginate
    conversations = query.order_by('-last_message_at', '-started_at')[offset:offset+limit]
    
    return [
        {
            "id": str(conv.id),
            "agent_name": conv.agent.name,
            "agent_id": str(conv.agent.id),
            "customer_phone": conv.customer_phone,
            "customer_name": conv.customer_name,
            "channel": conv.channel,
            "status": conv.status,
            "started_at": conv.started_at,
            "ended_at": conv.ended_at,
            "last_message_at": conv.last_message_at,
            "message_count": conv.message_count,
            "sentiment_score": conv.sentiment_score
        }
        for conv in conversations
    ]


# Get Specific Conversation by CONVersation ID
@router.get("/{conversation_id}", response=ConversationDetailResponse, auth=auth)
def get_conversation(request, conversation_id: str):
    """Get a specific conversation with messages"""
    
    user = request.auth
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        agent__organization=user.organization
    )
    
    messages = Message.objects.filter(
        conversation=conversation
    ).order_by('created_at')
    
    return {
        "id": str(conversation.id),
        "agent_name": conversation.agent.name,
        "agent_id": str(conversation.agent.id),
        "customer_phone": conversation.customer_phone,
        "customer_name": conversation.customer_name,
        "channel": conversation.channel,
        "status": conversation.status,
        "started_at": conversation.started_at,
        "ended_at": conversation.ended_at,
        "last_message_at": conversation.last_message_at,
        "message_count": conversation.message_count,
        "sentiment_score": conversation.sentiment_score,
        'assigned_to': {
                'id': str(conversation.assigned_to.id),
                'email': conversation.assigned_to.email,
                'first_name': conversation.assigned_to.first_name,
                'last_name': conversation.assigned_to.last_name,
                'full_name': f"{conversation.assigned_to.first_name} {conversation.assigned_to.last_name}".strip() or conversation.assigned_to.email,
            } if conversation.assigned_to else None,
            'handed_off_at': conversation.handed_off_at.isoformat() if conversation.handed_off_at else None,
        "customer_metadata": conversation.customer_metadata,
        "metadata": conversation.metadata,
        "messages": [
            {
                "id": str(msg.id),
                "sender_type": msg.sender_type,
                "content": msg.content,
                "message_type": msg.message_type,
                "media_url": msg.media_url,
                "created_at": msg.created_at,
                "delivered_at": msg.delivered_at,
                "read_at": msg.read_at
            }
            for msg in messages
        ]
    }

@router.post("/{conversation_id}/messages", auth=auth)
def send_message(request, conversation_id: str, data: SendHumanAgentMessageRequest):
    """Send a message in a conversation"""
    from services.message_processor import MessageProcessor
    from django.utils import timezone
    
    user = request.auth
    message_text = data.content.strip()

    
    if not message_text:
        return {"error": "Message content is required"}, 400
    
    try:
        # Get conversation
        conversation = Conversation.objects.select_related('agent').get(
            id=conversation_id,
            agent__organization=user.organization
        )
        
        # Save message to DB
        message = Message.objects.create(
            conversation=conversation,
            sender_type='human',
            content=message_text,
            message_type='text'
        )
        
        # Update conversation
        conversation.last_message_at = timezone.now()
        conversation.message_count += 1
        conversation.save()
        
        # Send to customer using the sync method
        processor = MessageProcessor()
        sent = processor.send_human_message_sync(conversation_id, message_text)
        
        if not sent:
            logger.warning(f"Failed to send message to customer for conversation {conversation_id}")
        
        return {
            "id": str(message.id),
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "sent_to_customer": sent
        }
        
    except Conversation.DoesNotExist:
        return {"error": "Conversation not found"}, 404
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return {"error": str(e)}, 400


# End Conversation API
@router.post("/{conversation_id}/end", auth=auth)
def end_conversation(request, conversation_id: str):
    """End a conversation"""
    
    user = request.auth
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        agent__organization=user.organization
    )
    
    conversation.status = 'ended'
    conversation.ended_at = datetime.now()
    
    # Calculate resolution time
    if conversation.started_at:
        delta = conversation.ended_at - conversation.started_at
        conversation.resolution_time_seconds = int(delta.total_seconds())
    
    conversation.save()
    
    return {"message": "Conversation ended successfully"}


@router.post("/{conversation_id}/handoff", auth=auth)
def handoff_conversation(request, conversation_id: str):
    """Hand off conversation to human agent"""
    
    user = request.auth
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        agent__organization=user.organization
    )
    
    conversation.status = 'handed_off'
    conversation.handed_off_at = datetime.now()
    conversation.assigned_to = user
    conversation.save()
    
    # Create system message
    Message.objects.create(
        conversation=conversation,
        sender_type='system',
        content=f"Conversation handed off to {user.first_name} {user.last_name}"
    )
    
    return {"message": "Conversation handed off successfully"}

@router.post("/{conversation_id}/handoff_back_to_ai_agent", auth=auth)
def handoff_conversation_back_to_ai_agent(request, conversation_id: str):
    """Hand off conversation to human agent"""
    
    user = request.auth
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        agent__organization=user.organization
    )
    
    conversation.status = 'active'
    conversation.handed_off_at = datetime.now()
    conversation.assigned_to = None  # Clear assigned human agent

    conversation.save()
    
    # Create system message
    Message.objects.create(
        conversation=conversation,
        sender_type='system',
        content=f"Conversation handed back to AI agent"
    )
    
    return {"message": "Conversation handed back to AI agent successfully"}



@router.post("/{conversation_id}/tags", auth=auth)
def add_tags(request, conversation_id: str, tags: List[str]):
    """Add tags to a conversation"""
    
    user = request.auth
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        agent__organization=user.organization
    )
    
    # Add tags (merge with existing)
    existing_tags = conversation.tags or []
    conversation.tags = list(set(existing_tags + tags))
    conversation.save()
    
    return {"tags": conversation.tags}


##### EXPORT Converstations Endpoints #####
# TODO 1:/conversations frontend export 
# 1. Export all conversations of a user's organization, 
# inputs: format: json or csv, date range, status, channel, agent_id

# TODO 2:/conversations/[id]/export
# 1. Export specific conversation history - showing messages, metadata, etc. inputs: format: json or csv, conversation_id

# TODO 3: /conversations/export
# Export conversations
@router.post("/export", auth=auth)
def export_conversations(request, params: ConversationSearchParams, format: str = 'json'):
    """Export conversations to JSON or CSV"""
    import csv
    import io
    import json
    from django.http import HttpResponse
    
    # Use the same search logic
    search_result = search_conversations(request, params)
    conversations = search_result['conversations']
    
    if format == 'csv':
        # Create CSV response
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'customer_phone', 'customer_name', 'channel', 
            'status', 'agent_name', 'started_at', 'message_count'
        ])
        writer.writeheader()
        
        for conv in conversations:
            writer.writerow({
                'id': conv['id'],
                'customer_phone': conv['customer_phone'],
                'customer_name': conv['customer_name'],
                'channel': conv['channel'],
                'status': conv['status'],
                'agent_name': conv['agent_name'],
                'started_at': conv['started_at'],
                'message_count': conv['message_count'],
            })
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="conversations.csv"'
        return response
    
    else:
        # Return JSON
        return {
            'export_date': datetime.now().isoformat(),
            'total_conversations': len(conversations),
            'conversations': conversations,
        }