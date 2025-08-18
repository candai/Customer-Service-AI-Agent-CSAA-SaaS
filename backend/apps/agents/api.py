# apps/agents/api.py
from ninja import Router, Schema, File
from ninja.files import UploadedFile
from typing import List, Optional
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Agent, AgentTemplate, KnowledgeDocument
from apps.accounts.api import auth
import hashlib
import PyPDF2
import csv
import io
import json
from .schemas import *
from django.db import models


import logging

logger = logging.getLogger(__name__)

# API Router for Agents
router = Router(tags=["Agents"])

############ AGENT API Endpoints #############
@router.post("/", response={200: AgentIDNameResponse, 400: ErrorSchema}, auth=auth)
@transaction.atomic
def create_agent(request, data: AgentCreateSchema):
    """Create a new AI agent"""
    
    user = request.auth
    if not user.organization:
        return 400, {"detail": "User does not belong to any organization", "code": 400}

    # Create agent
    #TODO: Validate agent name uniqueness within organization, number uniqueness for WhatsApp/SMS/Voice
    try:
        agent = Agent.objects.create(
            organization=request.auth.organization,
            **data.dict()
        )
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        return 400, {"detail": "Failed to create agent", "code": 400}
    
    # TODO: Provision phone numbers from Twilio
    # For now, using placeholder numbers
    # if data.whatsapp_enabled:
    #     agent.whatsapp_number = f"+1555{agent.id.hex[:7]}"
    # if data.sms_enabled:
    #     agent.sms_number = f"+1556{agent.id.hex[:7]}"
    # if data.voice_enabled:
    #     agent.voice_number = f"+1557{agent.id.hex[:7]}"
    
    # agent.save()
    
    return 200, {
        "id": str(agent.id),
        "name": agent.name
    }

@router.get("/", auth=auth)
def list_agents(request):
    """List all agents for the organization"""
    
    user = request.auth
    agents = Agent.objects.filter(organization=user.organization).order_by('-created_at')
    
    response = []
    for agent in agents:
        response.append({
            'id': str(agent.id),
            'name': agent.name,
            'description': agent.description or '',
            'is_active': agent.is_active,
            'whatsapp_enabled': agent.whatsapp_enabled,
            'whatsapp_number': agent.whatsapp_number or '',
            'sms_enabled': agent.sms_enabled,
            'sms_number': agent.sms_number or '',
            'voice_enabled': agent.voice_enabled,
            'voice_number': agent.voice_number or '',
            'voice_id': agent.voice_id or None,
            'system_prompt': agent.system_prompt,
            'welcome_message': agent.welcome_message or 'Hello! How can I help you today?',
            'model': agent.model,
            'temperature': agent.temperature,
            'max_tokens': agent.max_tokens,
            'total_conversations': agent.total_conversations,
            'total_messages': agent.total_messages,
            'language': agent.language or 'en',
            'personality_traits': agent.personality_traits or '',
            'created_at': agent.created_at.isoformat() if agent.created_at else None,
            'response_delay_seconds': agent.response_delay_seconds if hasattr(agent, 'response_delay_seconds') else 1,
        })
    
    return response


@router.get("/{agent_id}", auth=auth)
def get_agent(request, agent_id: str):
    """Get a specific agent"""
    
    user = request.auth
    try:
        agent = Agent.objects.get(id=UUID(agent_id), organization=user.organization)
        
        return {
            'id': str(agent.id),
            'name': agent.name,
            'description': agent.description or '',
            'is_active': agent.is_active,
            'whatsapp_enabled': agent.whatsapp_enabled,
            'whatsapp_number': agent.whatsapp_number or '',
            'sms_enabled': agent.sms_enabled,
            'sms_number': agent.sms_number or '',
            'voice_enabled': agent.voice_enabled,
            'voice_number': agent.voice_number or '',
            'voice_id': agent.voice_id or None,
            'system_prompt': agent.system_prompt,
            'welcome_message': agent.welcome_message or 'Hello! How can I help you today?',
            'model': agent.model,
            'temperature': agent.temperature,
            'max_tokens': agent.max_tokens,
            'language': agent.language or 'en',
            'personality_traits': agent.personality_traits or '',
            'response_delay_seconds': agent.response_delay_seconds if hasattr(agent, 'response_delay_seconds') else 1,
            'created_at': agent.created_at.isoformat() if agent.created_at else None,
        }
    except Agent.DoesNotExist:
        return 404, {"detail": "Agent not found", "code": 404}

    
    

@router.patch("/{agent_id}", auth=auth)
def patch_agent(request, agent_id: str, data: AgentUpdateSchema):
    """Partially update an agent"""
    from uuid import UUID
    
    user = request.auth
    try:
        agent = Agent.objects.get(
            id=UUID(agent_id),
            organization=user.organization
        )
        
        # Update only provided fields
        update_data = data.dict(exclude_unset=True)  # Only include fields that were actually sent
        
        for field, value in update_data.items():
            if hasattr(agent, field):
                # Handle empty strings for optional phone number fields
                if field in ['whatsapp_number', 'sms_number', 'voice_number', 'voice_id'] and value == '':
                    value = None
                setattr(agent, field, value)
        
        agent.save()
        
        logger.info(f"Agent {agent.name} updated by {user.email}")
        
        return {'success': True}
        
    except Agent.DoesNotExist:
        return 404, {"error": "Agent not found"}
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        return 400, {"error": str(e)}
    

@router.delete("/{agent_id}", 
    response= {200: SuccessResponse, 404: ErrorSchema},
    auth=auth)
def delete_agent(request, agent_id: str):
    """Delete an agent"""

    user = request.auth
    try:
        agent = Agent.objects.get(id=UUID(agent_id), organization=user.organization)
        agent.delete()
        return 200, {'success': True}
    except Agent.DoesNotExist:
        return 404, {"error": "Agent not found"}
    

@router.post("/{agent_id}/activate",
    response= {200: SuccessResponse, 404: ErrorSchema},
    auth=auth)
def activate_agent(request, agent_id: str):
    """Activate an agent"""
    
    user = request.auth
    try:
        agent = Agent.objects.get(id=UUID(agent_id), organization=user.organization)
        agent.is_active = True
        agent.save()
        return 200, {'succcess': True}
    except Agent.DoesNotExist:
        return 404, {"error": "Agent not found"}


@router.post("/{agent_id}/deactivate",
    response= {200: SuccessResponse, 404: ErrorSchema},
    auth=auth)
def deactivate_agent(request, agent_id: str):
    """Deactivate an agent"""
    
    user = request.auth
    try:
        agent = Agent.objects.get(id=UUID(agent_id), organization=user.organization)
        agent.is_active = False
        agent.save()
        return 200, {'succcess': True}
    except Agent.DoesNotExist:
        return 404, {"error": "Agent not found"}
    

######## Knowledge Document Management Endpoints ############ 
# Knowledge Management
@router.post("/{agent_id}/knowledge", response={201: KnowledgeDocumentResponse}, auth=auth)
def upload_knowledge(request, agent_id: str, file: UploadedFile = File(...), title: str = None, description: str = ""):
    """Upload a knowledge document for an agent"""
    
    user = request.auth
    agent = get_object_or_404(Agent, id=UUID(agent_id), organization=user.organization)
    
    # Process the file based on type
    content = ""
    file_content = file.read()
    
    if file.content_type == 'application/pdf':
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        for page in pdf_reader.pages:
            content += page.extract_text() + "\n"
        doc_type = 'pdf'
    
    elif file.content_type == 'text/csv':
        # Parse CSV
        csv_content = file_content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        content = json.dumps(rows, indent=2)
        doc_type = 'csv'
    
    elif file.content_type == 'application/json':
        # Parse JSON
        content = file_content.decode('utf-8')
        doc_type = 'json'
    
    else:
        # Plain text
        content = file_content.decode('utf-8')
        doc_type = 'text'
    
    # Calculate content hash to detect duplicates
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    
    # Check for duplicates
    if KnowledgeDocument.objects.filter(agent=agent, content_hash=content_hash).exists():
        return 400, {"error": "This document has already been uploaded"}
    
    # Create knowledge document
    doc = KnowledgeDocument.objects.create(
        agent=agent,
        title=title or file.name,
        description=description,
        document_type=doc_type,
        content=content,
        content_hash=content_hash,
        is_processed=True,
        processed_at=datetime.now()
    )
    
    # Save the file
    doc.file.save(file.name, file)
    
    return 201, {
        "id": str(doc.id),
        "title": doc.title,
        "description": doc.description,
        "document_type": doc.document_type,
        "is_processed": doc.is_processed,
        "uploaded_at": doc.uploaded_at,
        "content_preview": content[:200] + "..." if len(content) > 200 else content
    }

@router.get("/{agent_id}/knowledge", response=List[KnowledgeDocumentResponse], auth=auth)
def list_knowledge_documents(request, agent_id: str):
    """List all knowledge documents for an agent"""
    
    user = request.auth
    agent = get_object_or_404(Agent, id=UUID(agent_id), organization=user.organization)
    
    documents = KnowledgeDocument.objects.filter(agent=agent).order_by('-uploaded_at')
    
    return [
        {
            "id": str(doc.id),
            "title": doc.title,
            "description": doc.description,
            "document_type": doc.document_type,
            "is_processed": doc.is_processed,
            "uploaded_at": doc.uploaded_at,
            "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
        }
        for doc in documents
    ]

@router.delete("/{agent_id}/knowledge/{document_id}", auth=auth)
def delete_knowledge_document(request, agent_id: str, document_id: str):
    """Delete a knowledge document"""
    
    user = request.auth
    agent = get_object_or_404(Agent, id=UUID(agent_id), organization=user.organization)
    doc = get_object_or_404(KnowledgeDocument, id=document_id, agent=agent)
    
    # Delete file if exists
    if doc.file:
        doc.file.delete()
    
    doc.delete()
    
    return {"message": "Document deleted successfully"}



# Agent Template Endpoints
# Agent Templates Endpoints
@router.get("/templates/", auth=auth)
def list_agent_templates(request):
    """List available agent templates"""
    from apps.agents.models import AgentTemplate
    
    # Get public templates and organization-specific templates
    templates = AgentTemplate.objects.filter(
        models.Q(is_public=True) | 
        models.Q(organization=request.auth.organization)
    ).order_by('category', 'name')
    
    return [
        {
            'id': str(template.id),
            'name': template.name,
            'description': template.description,
            'category': template.category,
            'system_prompt': template.system_prompt,
            'personality_traits': template.personality_traits,
            'suggested_knowledge': template.suggested_knowledge,
            'is_public': template.is_public,
        }
        for template in templates
    ]



@router.post("/create-from-template/", auth=auth)
def create_agent_from_template(request, data: CreateFromTemplateRequest):
    """Create a new agent from a template"""
    
    logger = logging.getLogger(__name__)
    
    # Log the incoming data for debugging
    logger.info(f"Create from template data: {data}")
    
    # Extract all parameters from the request body
    template_id = data.template_id
    name = data.name
    description = data.description
    
    if not template_id or not name:
        return 400, {"error": "template_id and name are required"}
    
    try:
        template = AgentTemplate.objects.get(
            (
            models.Q(is_public=True) | 
            models.Q(organization=request.auth.organization)), id=UUID(template_id)
        )

        # Create agent from template
        agent = Agent.objects.create(
            organization=request.auth.organization,
            name=name,
            description=description or template.description,
            system_prompt=template.system_prompt,
            personality_traits=template.personality_traits,
            model='gpt-3.5-turbo',
            temperature=0.7,
            max_tokens=500,
            language='en',
            welcome_message="Hello! How can I help you today?",
            response_delay_seconds=1,
        )
        
        logger.info(f"Agent created: {agent.id} - {agent.name}")
        
        return {
            'id': str(agent.id),
            'name': agent.name,
            'message': f'Agent created from template: {template.name}'
        }
        
    except AgentTemplate.DoesNotExist:
        logger.error(f"Template not found: {template_id}")
        return 404, {"error": "Template not found"}
    except Exception as e:
        logger.error(f"Error creating agent from template: {e}")
        return 400, {"error": str(e)}


# Voice Preview Endpoint
@router.post("/{agent_id}/preview-voice", auth=auth)
def preview_agent_voice(request, agent_id: str, data: VoicePreviewRequest):  # Accept dict
    """Generate a voice preview for the agent"""
    from uuid import UUID
    import base64
    
    text = data.text
    if not text:
        return 400, {"error": "Text is required for voice preview"}
    
    try:
        agent = Agent.objects.get(
            id=UUID(agent_id),
            organization=request.auth.organization
        )
        
        if not agent.voice_enabled:
            return 400, {"error": "Voice is not enabled for this agent"}
        
        # TODO: Integrate with ElevenLabs API
        # For now, return a proper mock response
        
        # Remove after implementing actual voice generation
        mock_audio_base64 = "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qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq//PkxAAAAANIAAAAAExBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqTEFNRTMuMTAwqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"
        
        
        return {
            'agent_name': agent.name,
            'voice_id': agent.voice_id or 'default',
            'text': text,
            'audio_url': f"data:audio/wav;base64,{mock_audio_base64}",
            'duration_seconds': 3.5
        }
        
    except Agent.DoesNotExist:
        return 404, {"error": "Agent not found"}
    except Exception as e:
        logger.error(f"Voice preview error: {e}")
        return 400, {"error": str(e)}


#! Test Chat Endpoint (Real AI Response)
@router.post("/{agent_id}/test-chat", auth=auth)
def test_agent_chat(request, agent_id: str, data: TestChatRequest):
    """Test chat with actual AI response"""
    from uuid import UUID
    import openai
    from django.conf import settings
    
    message = data.message
    if not message:
        return 400, {"error": "Message is required"}
    
    try:
        agent = Agent.objects.get(
            id=UUID(agent_id),
            organization=request.auth.organization
        )
        
        #! TODO: Fix this
        # Use AI service to get response
        try:
            # TODO: Integrate with AI service
            # For now, return a mock response
            ai_response = f"[Mock Response] As {agent.name}, I would help you with: {message}"
            tokens_used = len(message.split()) * 2

            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            # Fallback to mock response
            ai_response = f"[Mock Response] As {agent.name}, I would help you with: {message}"
            tokens_used = len(message.split()) * 2
        
        return {
            'agent_name': agent.name,
            'user_message': message,
            'agent_response': ai_response,
            'model_used': agent.model,
            'tokens_used': tokens_used
        }
        
    except Agent.DoesNotExist:
        return 404, {"error": "Agent not found"}
    except Exception as e:
        logger.error(f"Test chat error: {e}")
        return 400, {"error": str(e)}
        
    except Agent.DoesNotExist:
        return 404, {"error": "Agent not found"}




#! Test Endpoints
@router.post("/{agent_id}/test-message", auth=auth)
def test_agent_message(request, agent_id: str, data: TestChatRequest):
    """Test agent with a message (dry run)"""

    message = data.message
    if not message:
        return 400, {"error": "Message is required"}
    
    user = request.auth
    agent = get_object_or_404(Agent, id=UUID(agent_id), organization=user.organization)
    
    # TODO: Integrate with AI service
    # For now, return a mock response
    mock_response = f"[{agent.name}]: Thank you for your message: '{message}'. This is a test response based on my configuration."
    
    return {
        "agent_name": agent.name,
        "user_message": message,
        "agent_response": mock_response,
        "model_used": agent.model,
        "tokens_used": len(message.split()) * 2  # Mock token count
    }


#! Test Call Endpoint (Voice)
@router.post("/{agent_id}/test-call", auth=auth)
def test_agent_call(request, agent_id: str, data: TestCallRequest):  # Accept dict
    """Initiate a test call to the agent"""
    
    phone_number = data.phone_number
    
    if not phone_number:
        return 400, {"error": "Phone number is required"}
    
    # parse phone number using hex
    # +1 handling, default to US format
    
    try:
        agent = Agent.objects.get(
            id=UUID(agent_id),
            organization=request.auth.organization
        )
        
        if not agent.voice_enabled:
            return 400, {"error": "Voice calls are not enabled for this agent"}
        
        #! TODO: Integrate with AI service
        #! TODO: Integrate with Twilio to make actual call
        
        # For now, return mock response
        return 200, {
            "message": "Test call initiated",
            "to_number": phone_number,
            "agent_name": agent.name,
            "call_sid": f"CALL_{agent.id.hex[:10]}"  # Mock call SID
        }
        
    except Agent.DoesNotExist:
        return 404, {"error": "Agent not found"}
    except Exception as e:
        logger.error(f"Test call error: {e}")
        return 400, {"error": str(e)}