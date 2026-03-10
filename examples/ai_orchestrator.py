"""
AI Orchestrator Example
Demonstrates multi-LLM orchestration with automatic failover using LangChain and Supabase.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import base64
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from supabase import create_client, Client

# ============================================
# Encryption Service (AES-256-GCM)
# ============================================
class EncryptionService:
    """Service for encrypting/decrypting API keys"""
    
    def __init__(self):
        key_b64 = os.environ.get("ENCRYPTION_KEY")
        if not key_b64:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        self.key = base64.b64decode(key_b64)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt text using AES-256-GCM"""
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt text"""
        data = base64.b64decode(ciphertext)
        nonce = data[:12]
        ciphertext = data[12:]
        aesgcm = AESGCM(self.key)
        return aesgcm.decrypt(nonce, ciphertext, None).decode()

# ============================================
# AI Model Orchestrator
# ============================================
class AIOrchestrator:
    """Orchestrator for working with different AI providers with automatic failover"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.encryption = EncryptionService()
        self._providers_cache = {}
        self._models_cache = {}
        self._last_refresh = None
    
    async def get_model_for_task(self, tenant_id: str, task_type: str) -> Dict:
        """
        Get configured model for specific tenant and task type.
        
        Args:
            tenant_id: UUID of the tenant
            task_type: Type of task (e.g., 'comment_classification', 'reply_generation')
            
        Returns:
            Dict with model configuration including provider and fallback
        """
        config = self.supabase.table("tenant_ai_configs")\
            .select("*, model_id(*, provider_id(*)), fallback_model_id(*, provider_id(*))")\
            .eq("tenant_id", tenant_id)\
            .eq("task_type", task_type)\
            .eq("is_active", True)\
            .execute()
        
        if config.data:
            return config.data[0]
        
        # If no custom settings, get defaults
        return await self._get_default_config(task_type)
    
    async def execute_with_failover(
        self,
        tenant_id: str,
        task_type: str,
        messages: List[Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute request to AI with automatic failover on errors.
        
        Args:
            tenant_id: UUID of the tenant
            task_type: Type of task
            messages: List of LangChain messages
            **kwargs: Additional parameters
            
        Returns:
            Dict with response content, model info, and token usage
        """
        # Get configuration
        config = await self.get_model_for_task(tenant_id, task_type)
        
        # Log start
        start_time = datetime.now()
        
        # Try main model
        try:
            result = await self._call_model(config, messages, kwargs)
            
            # Log success
            await self._log_usage(
                tenant_id=tenant_id,
                task_type=task_type,
                provider_id=config["model_id"]["provider_id"]["id"],
                model_id=config["model_id"]["id"],
                prompt_tokens=result["tokens"]["prompt"],
                completion_tokens=result["tokens"]["completion"],
                response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                status="success"
            )
            return result
            
        except Exception as e:
            # Log error
            await self._log_usage(
                tenant_id=tenant_id,
                task_type=task_type,
                provider_id=config["model_id"]["provider_id"]["id"],
                model_id=config["model_id"]["id"],
                prompt_tokens=0,
                completion_tokens=0,
                response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                status="error",
                error_message=str(e)
            )
            
            # If fallback model exists, try it
            if config.get("fallback_model_id"):
                fallback_config = {
                    "model_id": config["fallback_model_id"],
                    "temperature": config.get("temperature", 0.7),
                    "max_tokens": config.get("max_tokens")
                }
                fallback_result = await self._call_model(fallback_config, messages, kwargs)
                
                # Log fallback
                await self._log_usage(
                    tenant_id=tenant_id,
                    task_type=task_type,
                    provider_id=fallback_config["model_id"]["provider_id"]["id"],
                    model_id=fallback_config["model_id"]["id"],
                    prompt_tokens=fallback_result["tokens"]["prompt"],
                    completion_tokens=fallback_result["tokens"]["completion"],
                    response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    status="failover"
                )
                return fallback_result
            else:
                raise
    
    async def _call_model(self, config: Dict, messages: List[Any], kwargs: Dict) -> Dict:
        """
        Call specific model via LangChain.
        
        Args:
            config: Model configuration dict
            messages: List of LangChain messages
            kwargs: Additional parameters
            
        Returns:
            Dict with response content and token usage
        """
        model = config["model_id"]
        provider = model["provider_id"]
        
        # Decrypt API key
        api_key = self.encryption.decrypt(provider["api_key_encrypted"])
        
        # Create appropriate LangChain client
        if provider["name"] == "nvidia":
            chat = ChatOpenAI(
                base_url=provider["base_url"],
                api_key=api_key,
                model=model["model_id"],
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", model["max_tokens"])
            )
        elif provider["name"] == "google":
            chat = ChatGoogleGenerativeAI(
                google_api_key=api_key,
                model=model["model_id"],
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", model["max_tokens"])
            )
        elif provider["name"] == "anthropic":
            chat = ChatAnthropic(
                anthropic_api_key=api_key,
                model=model["model_id"],
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", model["max_tokens"])
            )
        else:
            raise ValueError(f"Unknown provider: {provider['name']}")
        
        # Execute request
        response = await chat.agenerate([messages])
        
        # Count tokens (approximate)
        prompt_tokens = sum([len(m.content) / 4 for m in messages])
        completion_tokens = len(response.generations[0][0].text) / 4
        
        return {
            "content": response.generations[0][0].text,
            "model": model["model_id"],
            "provider": provider["name"],
            "tokens": {
                "prompt": int(prompt_tokens),
                "completion": int(completion_tokens),
                "total": int(prompt_tokens + completion_tokens)
            }
        }
    
    async def _log_usage(self, **kwargs):
        """Log usage for billing and monitoring"""
        await self.supabase.table("ai_usage_logs").insert(kwargs).execute()
    
    async def _get_default_config(self, task_type: str) -> Dict:
        """Get default configuration for a task type"""
        # This would fetch default config from database
        # For now, return a placeholder
        return {
            "model_id": {
                "id": "default-model-id",
                "provider_id": {
                    "id": "default-provider-id",
                    "name": "nvidia",
                    "base_url": "https://integrate.api.nvidia.com/v1"
                }
            },
            "temperature": 0.7,
            "max_tokens": 1000
        }

# ============================================
# Example Usage
# ============================================
async def main():
    """Example usage of AIOrchestrator"""
    # Initialize Supabase client
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    supabase = create_client(supabase_url, supabase_key)
    
    # Initialize orchestrator
    orchestrator = AIOrchestrator(supabase)
    
    # Example: Analyze comment sentiment
    tenant_id = "your-tenant-uuid"
    task_type = "comment_classification"
    
    messages = [
        SystemMessage(content="You are a helpful assistant that analyzes social media comments."),
        HumanMessage(content="This product is amazing! Best purchase ever!")
    ]
    
    try:
        result = await orchestrator.execute_with_failover(
            tenant_id=tenant_id,
            task_type=task_type,
            messages=messages
        )
        print(f"Response: {result['content']}")
        print(f"Model: {result['model']}")
        print(f"Tokens: {result['tokens']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
