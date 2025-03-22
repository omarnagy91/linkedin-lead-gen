from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class SearchQuery(BaseModel):
    """Model for search query stored in the database"""
    id: UUID
    job_id: UUID
    query: str
    company: str
    country: str
    status: str
    results_count: int = 0
    created_at: str


class ProfileUrl(BaseModel):
    """Model for LinkedIn profile URL stored in the database"""
    id: UUID
    job_id: UUID
    linkedin_url: HttpUrl
    company: str
    country: str
    search_snippet: Optional[str] = None
    status: str
    created_at: str


class EmploymentDates(BaseModel):
    """Model for employment dates"""
    join_date: Optional[str] = None
    departure_date: Optional[str] = None


class Profile(BaseModel):
    """Model for enriched profile stored in the database"""
    id: UUID
    job_id: UUID
    linkedin_url: HttpUrl
    profile_data: Dict
    job_title: Optional[str] = None
    company_specific_title: Optional[str] = None
    experience_years: Optional[float] = None
    meets_criteria: bool = False
    created_at: str


class TitleSelection(BaseModel):
    """Model for job title selection stored in the database"""
    id: UUID
    job_id: UUID
    title: str
    company: str
    count: int = 0
    selected: bool = False
    created_at: str


class Export(BaseModel):
    """Model for export stored in the database"""
    id: UUID
    job_id: UUID
    google_sheet_url: Optional[HttpUrl] = None
    status: str
    profiles_exported: int = 0
    created_at: str
    completed_at: Optional[str] = None


class Job(BaseModel):
    """Model for job stored in the database"""
    id: UUID
    user_email: str
    campaign_goal: Optional[str] = None
    company_urls: List[str]
    countries: List[str]
    employment_status: str
    decision_level: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
