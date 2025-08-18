from datetime import datetime
from typing import List, Optional
from ninja import Router, Schema
from uuid import UUID


class AgentUpdateSchema(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    language: Optional[str] = None
    personality_traits: Optional[str] = None
    whatsapp_enabled: Optional[bool] = None
    whatsapp_number: Optional[str] = None
    sms_enabled: Optional[bool] = None
    sms_number: Optional[str] = None
    voice_enabled: Optional[bool] = None
    voice_number: Optional[str] = None
    voice_id: Optional[str] = None
    response_delay_seconds: Optional[int] = None
    is_active: Optional[bool] = None

# Schemas
class AgentCreateSchema(Schema):
    name: str
    description: str
    system_prompt: str
    welcome_message: str = "Hello! How can I help you today?"
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 500
    language: str = "en"
    personality_traits: str
    whatsapp_enabled: bool = False
    whatsapp_number: str = ""
    sms_enabled: bool = False
    sms_number: str = ""
    voice_enabled: bool = False
    voice_number: str = ""
    voice_id: Optional[str] = None
    response_delay_seconds: int = 1
    
class AgentIDNameResponse(Schema):
    id: UUID
    name: str

class SuccessResponse(Schema):
    success: bool

class ErrorSchema(Schema):
    error: str

class AgentResponse(Schema):
    id: UUID
    name: str
    description: str
    personality_traits: str
    system_prompt: str
    whatsapp_enabled: bool
    whatsapp_number: Optional[str] = None
    sms_enabled: bool
    sms_number: Optional[str] = None
    voice_enabled: bool
    voice_number: Optional[str] = None
    voice_id: Optional[str] = None
    is_active: bool
    total_conversations: int
    total_messages: int
    created_at: Optional[datetime] = None
    language: str
    welcome_message: str
    model: str
    temperature: float
    max_tokens: int
    response_delay_seconds: Optional[int] = None



class KnowledgeDocumentResponse(Schema):
    id: UUID
    title: str
    description: str
    document_type: str
    is_processed: bool
    uploaded_at: datetime
    content_preview: str

# backend/apps/agents/schemas.py
# Add these schemas

from typing import Optional
from ninja import Schema

class TestChatRequest(Schema):
    message: str

class TestChatResponse(Schema):
    agent_name: str
    user_message: str
    agent_response: str
    model_used: str
    tokens_used: int

class VoicePreviewRequest(Schema):
    text: str = "Hello, I'm your AI assistant. How can I help you today?"

class VoicePreviewResponse(Schema):
    agent_name: str
    voice_id: str
    text: str
    audio_url: str
    duration_seconds: float

class TestCallRequest(Schema):
    phone_number: str

class TestCallResponse(Schema):
    message: str
    to_number: str
    agent_name: str
    call_sid: str

class CreateFromTemplateRequest(Schema):
    template_id: str
    name: str
    description: Optional[str] = ""