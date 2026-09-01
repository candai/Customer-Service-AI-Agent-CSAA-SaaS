from ninja import Router, Schema
from datetime import datetime
from typing import Optional, List

class AnalyticsParams(Schema):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    agent_uuid_string: Optional[str] = None
    channel: Optional[str] = None
    granularity: Optional[str] = 'day'  # hour, day, week, month

class AnalyticsResponse(Schema):
    summary: dict
    trends: List[dict]
    channel_distribution: List[dict]
    agent_performance: List[dict]
    peak_hours: List[dict]
    response_times: dict
    customer_satisfaction: dict