import os
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseSettings, validator

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API configuration
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_KEY: str
    
    # Supabase configuration
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # External API keys
    OPENAI_API_KEY: str
    SERPAPI_API_KEY: str
    PROXYCURL_API_KEY: str
    
    # Google Sheets API
    GOOGLE_API_CREDENTIALS: str
    GOOGLE_SHEET_ID: str
    
    # Service configuration
    MAX_SEARCH_WORKERS: int = 5
    MAX_ENRICHMENT_WORKERS: int = 10
    REQUEST_TIMEOUT: int = 30
    CACHE_EXPIRY: int = 86400  # 24 hours in seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @validator("API_KEY")
    def validate_api_key(cls, v):
        """Validate that API key is provided"""
        if not v:
            raise ValueError("API_KEY must be provided")
        return v
    
    @validator("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY")
    def validate_supabase_config(cls, v, values, **kwargs):
        """Validate that Supabase configuration is provided"""
        if not v:
            raise ValueError(f"{kwargs['field'].name} must be provided")
        return v
    
    @validator("OPENAI_API_KEY", "SERPAPI_API_KEY", "PROXYCURL_API_KEY")
    def validate_api_keys(cls, v, values, **kwargs):
        """Validate that API keys are provided"""
        if not v:
            raise ValueError(f"{kwargs['field'].name} must be provided")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
