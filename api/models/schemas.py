"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class TaskType(str, Enum):
    """Types of AI tasks supported by the platform."""
    COMMENT_CLASSIFICATION = "comment_classification"
    REPLY_GENERATION = "reply_generation"
    NPS_CALCULATION = "nps_calculation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"


class DraftStatus(str, Enum):
    """Status of a draft response."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class ChatRequest(BaseModel):
    """Request to AI agent for chat/response generation."""
    messages: List[Dict[str, str]] = Field(
        ...,
        description="List of messages in format [{'role': 'user', 'content': 'text'}]"
    )
    task_type: Optional[TaskType] = TaskType.COMMENT_CLASSIFICATION
    tenant_id: Optional[str] = None
    stream: bool = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000


class ChatResponse(BaseModel):
    """Response from AI agent."""
    reply: str
    model_used: str
    provider: str
    tokens_used: Dict[str, int]
    processing_time_ms: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    supabase_connected: bool


class CommentAnalysisRequest(BaseModel):
    """Request to analyze a comment."""
    comment_text: str
    platform: str  # 'instagram', 'youtube', 'tiktok'
    tenant_id: Optional[str] = None


class CommentAnalysisResponse(BaseModel):
    """Response with comment analysis results."""
    sentiment_score: float  # 0-10
    category: str  # 'promoter', 'neutral', 'detractor'
    confidence: float
    suggested_reply: Optional[str] = None
    nps_category: str


# Approval Workflow Schemas
class DraftResponse(BaseModel):
    """Draft response model."""
    id: str
    tenant_id: str
    comment_id: str
    comment_text: str
    platform: str
    platform_comment_id: Optional[str] = None
    platform_post_id: Optional[str] = None
    ai_generated_reply: str
    original_sentiment_score: Optional[int] = None
    original_nps_category: Optional[str] = None
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    published_comment_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DraftCreate(BaseModel):
    """Request to create a new draft."""
    tenant_id: str
    comment_id: str
    comment_text: str
    platform: str
    platform_comment_id: Optional[str] = None
    platform_post_id: Optional[str] = None
    ai_generated_reply: str
    sentiment_score: Optional[int] = None
    nps_category: Optional[str] = None


class DraftApprove(BaseModel):
    """Request to approve a draft."""
    draft_id: str
    notes: Optional[str] = None


class DraftReject(BaseModel):
    """Request to reject a draft."""
    draft_id: str
    reason: str


class DraftPublish(BaseModel):
    """Request to publish a draft."""
    draft_id: str
