from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Model for error responses"""
    error: bool = True
    message: str
    code: str


class SearchResult(BaseModel):
    """Model for search result from SerpAPI"""
    title: str
    url: str
    snippet: Optional[str] = None


class EnrichmentResult(BaseModel):
    """Model for profile enrichment result from ProxyCurl"""
    success: bool
    profile_url: str
    error_message: Optional[str] = None


class QueueStats(BaseModel):
    """Model for queue statistics"""
    queue_name: str
    pending_tasks: int
    active_tasks: int
    completed_tasks: int
    failed_tasks: int


class SystemStatus(BaseModel):
    """Model for system status"""
    is_healthy: bool
    api_credits: Dict[str, int]
    active_jobs: int
    queue_stats: List[QueueStats]
    version: str
