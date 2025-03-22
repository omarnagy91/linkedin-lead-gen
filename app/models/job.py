from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl, validator


class EmploymentStatus(str, Enum):
    CURRENT = "current"
    PAST = "past"
    ALL = "all"


class JobStatus(str, Enum):
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    AWAITING_SELECTION = "awaiting_selection"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"


class Company(BaseModel):
    """Company model for job creation"""
    company_url: HttpUrl
    company_name: str


class JobCreate(BaseModel):
    """Model for creating a new job"""
    user_email: EmailStr
    campaign_goal: Optional[str] = None
    company_urls: List[HttpUrl]
    countries: List[str]
    employment_status: EmploymentStatus
    decision_level: Optional[str] = None
    
    @validator('countries')
    def validate_countries(cls, countries):
        """Validate that countries are provided"""
        if not countries:
            raise ValueError("At least one country must be specified")
        return countries
    
    @validator('company_urls')
    def validate_company_urls(cls, company_urls):
        """Validate that company URLs are provided"""
        if not company_urls:
            raise ValueError("At least one company URL must be specified")
        return company_urls


class JobResponse(BaseModel):
    """Response model for job creation"""
    job_id: UUID
    status: JobStatus
    message: str


class JobProgressStats(BaseModel):
    """Statistics about job progress"""
    searches_completed: int
    searches_total: int
    profiles_discovered: int
    profiles_enriched: int


class JobStatus(BaseModel):
    """Model for job status response"""
    job_id: UUID
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    progress: Optional[JobProgressStats] = None


class TitleCount(BaseModel):
    """Model for job title counts"""
    company: str
    title: str
    count: int
    selected: bool = False


class TitleList(BaseModel):
    """Model for job title list response"""
    job_id: UUID
    titles: List[TitleCount]


class TitleSelection(BaseModel):
    """Model for selecting job titles"""
    titles: List[TitleCount]


class TitleSelectionResponse(BaseModel):
    """Response model for title selection"""
    job_id: UUID
    status: JobStatus
    message: str


class ExportStatus(BaseModel):
    """Model for export status response"""
    job_id: UUID
    status: str
    export_url: Optional[HttpUrl] = None
    profiles_exported: int = 0
    completed_at: Optional[datetime] = None
