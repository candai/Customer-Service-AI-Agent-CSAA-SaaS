from datetime import datetime
from typing import List, Optional
from ninja import Schema

class MessageResponse(Schema):
    id: str
    sender_type: str
    content: str
    message_type: str
    media_url: Optional[str]
    created_at: datetime
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]

class ConversationResponse(Schema):
    id: str
    agent_name: str
    agent_id: str
    customer_phone: str
    customer_name: Optional[str]
    channel: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    last_message_at: Optional[datetime]
    message_count: int
    sentiment_score: Optional[float]

class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse]
    customer_metadata: dict
    metadata: dict

class ConversationStatsResponse(Schema):
    total_conversations: int
    active_conversations: int
    total_messages: int
    total_agents: int
    response_time_avg: float
    satisfaction_score: float

class ConversationSearchParams(Schema):
    query: Optional[str] = None
    status: Optional[str] = None
    channel: Optional[str] = None
    agent_id: Optional[str] = None
    customer_phone: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_handoff: Optional[bool] = None
    min_messages: Optional[int] = None
    max_messages: Optional[int] = None
    sort_by: Optional[str] = 'last_message_at'  # last_message_at, started_at, message_count
    order: Optional[str] = 'desc'  # asc, desc
    limit: Optional[int] = 50
    offset: Optional[int] = 0

class ConversationSearchResponse(Schema):
    conversations: List[dict]
    total: int
    filtered: int
    page_size: int
    page: int

class SendHumanAgentMessageRequest(Schema):
    content: str
    sender_type: str = "human"  # Optional with default
