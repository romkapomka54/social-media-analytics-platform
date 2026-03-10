"""
Application settings and configuration.
"""
from pydantic_settings import BaseSettings
from typing import Optional
from supabase import create_client, Client


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Social Media Analytics Platform"
    debug: bool = False
    
    # Supabase
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str
    
    # Encryption
    encryption_key: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def supabase_client(self) -> Client:
        """Get Supabase client instance."""
        return create_client(self.supabase_url, self.supabase_service_role_key)


# Global settings instance
settings = Settings()
