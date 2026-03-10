"""
Chat and AI interaction router with streaming support.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, AsyncGenerator
import json
import asyncio
import time
from datetime import datetime

from ..core.config import settings
from ..core.security import get_current_tenant
from ..models.schemas import ChatRequest, ChatResponse, CommentAnalysisRequest, CommentAnalysisResponse
from ..services.langchain_service import generate_chat_response, analyze_comment

router = APIRouter(prefix="/chat", tags=["chat"])


async def generate_stream(
    body: ChatRequest,
    tenant_id: str
) -> AsyncGenerator[str, None]:
    """Generate streaming response using SSE format."""
    start_time = time.time()
    
    try:
        # Use provided tenant_id or fallback
        effective_tenant_id = body.tenant_id or tenant_id
        if not effective_tenant_id:
            result = settings.supabase_client.table("tenants").select("id").limit(1).execute()
            if result.data:
                effective_tenant_id = result.data[0]["id"]
            else:
                raise HTTPException(status_code=400, detail="No tenants found")
        
        # Call AI service
        response_data = await generate_chat_response(
            messages=body.messages,
            tenant_id=effective_tenant_id,
            task_type=body.task_type.value,
            temperature=body.temperature,
            max_tokens=body.max_tokens
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Format SSE response
        chat_response = ChatResponse(
            reply=response_data["reply"],
            model_used=response_data["model_used"],
            provider=response_data["provider"],
            tokens_used=response_data["tokens_used"],
            processing_time_ms=processing_time
        )
        
        yield f"data: {json.dumps(chat_response.dict())}\n\n"
        
    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    yield "event: done\ndata: {}\n\n"


@router.post("/stream")
async def stream_chat(
    body: ChatRequest
):
    """
    Create streaming response from AI agent (SSE).
    """
    return StreamingResponse(
        generate_stream(body, None),
        media_type="text/event-stream"
    )


@router.post("/sync", response_model=ChatResponse)
async def sync_chat(
    body: ChatRequest
):
    """
    Synchronous response from AI agent.
    """
    effective_tenant_id = body.tenant_id
    if not effective_tenant_id:
        result = settings.supabase_client.table("tenants").select("id").limit(1).execute()
        if result.data:
            effective_tenant_id = result.data[0]["id"]
        else:
            raise HTTPException(status_code=400, detail="No tenants found")
    
    try:
        response_data = await generate_chat_response(
            messages=body.messages,
            tenant_id=effective_tenant_id,
            task_type=body.task_type.value,
            temperature=body.temperature,
            max_tokens=body.max_tokens
        )
        
        return ChatResponse(
            reply=response_data["reply"],
            model_used=response_data["model_used"],
            provider=response_data["provider"],
            tokens_used=response_data["tokens_used"],
            processing_time_ms=response_data["processing_time_ms"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest
):
    """
    Send a chat message to the AI agent (alias for /sync).
    """
    return await sync_chat(body)


@router.post("/analyze", response_model=CommentAnalysisResponse)
async def analyze_comment_endpoint(
    body: CommentAnalysisRequest
):
    """
    Analyze a social media comment for sentiment and NPS category.
    """
    effective_tenant_id = body.tenant_id
    if not effective_tenant_id:
        result = settings.supabase_client.table("tenants").select("id").limit(1).execute()
        if result.data:
            effective_tenant_id = result.data[0]["id"]
        else:
            raise HTTPException(status_code=400, detail="No tenants found")
    
    try:
        result = await analyze_comment(
            comment_text=request.comment_text,
            tenant_id=effective_tenant_id,
            task_type="comment_classification"
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Placeholder response (to be replaced with real AI output)
        return CommentAnalysisResponse(
            sentiment_score=7.5,
            category="neutral",
            confidence=0.85,
            suggested_reply="Thank you for your feedback!",
            nps_category="neutral"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
