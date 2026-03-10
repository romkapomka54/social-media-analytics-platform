"""
Health check router.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio

from ..core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    Returns status of the API and connected services.
    """
    supabase_connected = False
    
    try:
        # Test Supabase connection
        client = settings.supabase_client
        result = client.table("tenants").select("count", count="exact").execute()
        supabase_connected = True
    except Exception as e:
        print(f"Supabase connection error: {e}")
        supabase_connected = False
    
    return {
        "status": "healthy" if supabase_connected else "degraded",
        "version": "1.0.0",
        "supabase_connected": supabase_connected
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.
    Returns whether the service is ready to accept traffic.
    """
    # Add more checks as needed (database, AI providers, etc.)
    return {
        "ready": True,
        "checks": {
            "supabase": True  # TODO: Add actual check
        }
    }
