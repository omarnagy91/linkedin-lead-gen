import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from supabase import Client, create_client

from app.models.database import (
    Export, 
    Job, 
    Profile, 
    ProfileUrl, 
    SearchQuery, 
    TitleSelection
)
from app.models.job import JobCreate, JobProgressStats, JobStatus, TitleCount
from app.utils.config import settings

logger = logging.getLogger(__name__)

# Global client instance
_supabase_client = None


def get_supabase_client() -> Client:
    """
    Get or create a Supabase client with connection pooling.
    
    Returns:
        Client: Configured Supabase client
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
            options={
                'headers': {
                    'Authorization': f'Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}'
                },
                'pool_size': 20,
                'max_overflow': 30,
                'pool_timeout': 30,
                'pool_recycle': 3600
            }
        )
    
    return _supabase_client


class DatabaseService:
    """Service for database operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def create_job(self, job_data: JobCreate) -> UUID:
        """
        Create a new job in the database.
        
        Args:
            job_data: Job creation data
            
        Returns:
            UUID: The created job ID
        """
        try:
            # Convert URLs to strings for storage
            company_urls = [str(url) for url in job_data.company_urls]
            
            # Insert job into database
            result = await self.supabase.table('jobs').insert({
                'user_email': job_data.user_email,
                'campaign_goal': job_data.campaign_goal,
                'company_urls': company_urls,
                'countries': job_data.countries,
                'employment_status': job_data.employment_status,
                'decision_level': job_data.decision_level,
                'status': JobStatus.SUBMITTED.value
            }).execute()
            
            # Extract and return the job ID
            job_id = result.data[0]['id']
            logger.info(f"Created job with ID: {job_id}")
            return UUID(job_id)
        
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise
    
    async def get_job(self, job_id: UUID) -> Job:
        """
        Get job details from the database.
        
        Args:
            job_id: The job ID
            
        Returns:
            Job: The job details
        """
        try:
            result = await self.supabase.table('jobs').select('*').eq('id', str(job_id)).execute()
            
            if not result.data:
                logger.error(f"Job not found: {job_id}")
                raise ValueError(f"Job not found: {job_id}")
            
            return Job(**result.data[0])
        
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {str(e)}")
            raise
    
    async def update_job_status(self, job_id: UUID, status: Union[JobStatus, str]) -> None:
        """
        Update the status of a job.
        
        Args:
            job_id: The job ID
            status: The new status
        """
        try:
            # Convert enum to string if needed
            status_value = status.value if isinstance(status, JobStatus) else status
            
            await self.supabase.table('jobs').update({
                'status': status_value,
                'updated_at': datetime.now().isoformat()
            }).eq('id', str(job_id)).execute()
            
            logger.info(f"Updated job {job_id} status to {status_value}")
        
        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")
            raise
    
    async def store_search_queries(
        self, job_id: UUID, queries: List[Dict[str, str]]
    ) -> List[UUID]:
        """
        Store search queries for a job.
        
        Args:
            job_id: The job ID
            queries: List of query dictionaries with company, country, and query
            
        Returns:
            List[UUID]: The created query IDs
        """
        try:
            # Prepare query data
            query_data = [
                {
                    'job_id': str(job_id),
                    'query': query['query'],
                    'company': query['company'],
                    'country': query['country'],
                    'status': 'pending'
                }
                for query in queries
            ]
            
            # Insert queries into database
            result = await self.supabase.table('search_queries').insert(query_data).execute()
            
            # Extract and return query IDs
            query_ids = [UUID(item['id']) for item in result.data]
            logger.info(f"Stored {len(query_ids)} search queries for job {job_id}")
            return query_ids
        
        except Exception as e:
            logger.error(f"Error storing search queries: {str(e)}")
            raise
    
    async def get_search_query(self, query_id: UUID) -> SearchQuery:
        """
        Get a search query from the database.
        
        Args:
            query_id: The query ID
            
        Returns:
            SearchQuery: The search query details
        """
        try:
            result = await self.supabase.table('search_queries').select('*').eq('id', str(query_id)).execute()
            
            if not result.data:
                logger.error(f"Search query not found: {query_id}")
                raise ValueError(f"Search query not found: {query_id}")
            
            return SearchQuery(**result.data[0])
        
        except Exception as e:
            logger.error(f"Error getting search query {query_id}: {str(e)}")
            raise
    
    async def update_search_query(
        self, query_id: UUID, status: str, results_count: Optional[int] = None
    ) -> None:
        """
        Update a search query.
        
        Args:
            query_id: The query ID
            status: The new status
            results_count: The number of results found
        """
        try:
            update_data = {'status': status}
            if results_count is not None:
                update_data['results_count'] = results_count
            
            await self.supabase.table('search_queries').update(update_data).eq('id', str(query_id)).execute()
            logger.info(f"Updated search query {query_id} status to {status}")
        
        except Exception as e:
            logger.error(f"Error updating search query: {str(e)}")
            raise
    
    async def check_url_exists(self, job_id: UUID, linkedin_url: str) -> bool:
        """
        Check if a LinkedIn URL already exists for a job.
        
        Args:
            job_id: The job ID
            linkedin_url: The LinkedIn URL
            
        Returns:
            bool: True if the URL exists, False otherwise
        """
        try:
            result = await self.supabase.table('profile_urls').select('id').eq('job_id', str(job_id)).eq('linkedin_url', linkedin_url).execute()
            return len(result.data) > 0
        
        except Exception as e:
            logger.error(f"Error checking URL existence: {str(e)}")
            raise
    
    async def store_profile_url(
        self, job_id: UUID, linkedin_url: str, company: str, country: str, search_snippet: Optional[str] = None
    ) -> UUID:
        """
        Store a LinkedIn profile URL.
        
        Args:
            job_id: The job ID
            linkedin_url: The LinkedIn profile URL
            company: The company name
            country: The country
            search_snippet: Optional search snippet
            
        Returns:
            UUID: The created profile URL ID
        """
        try:
            result = await self.supabase.table('profile_urls').insert({
                'job_id': str(job_id),
                'linkedin_url': linkedin_url,
                'company': company,
                'country': country,
                'search_snippet': search_snippet,
                'status': 'discovered'
            }).execute()
            
            url_id = result.data[0]['id']
            logger.info(f"Stored profile URL {linkedin_url} for job {job_id}")
            return UUID(url_id)
        
        except Exception as e:
            logger.error(f"Error storing profile URL: {str(e)}")
            raise
    
    async def get_profile_url(self, url_id: UUID) -> ProfileUrl:
        """
        Get a profile URL from the database.
        
        Args:
            url_id: The profile URL ID
            
        Returns:
            ProfileUrl: The profile URL details
        """
        try:
            result = await self.supabase.table('profile_urls').select('*').eq('id', str(url_id)).execute()
            
            if not result.data:
                logger.error(f"Profile URL not found: {url_id}")
                raise ValueError(f"Profile URL not found: {url_id}")
            
            return ProfileUrl(**result.data[0])
        
        except Exception as e:
            logger.error(f"Error getting profile URL {url_id}: {str(e)}")
            raise
    
    async def update_profile_url_status(self, url_id: UUID, status: str) -> None:
        """
        Update the status of a profile URL.
        
        Args:
            url_id: The profile URL ID
            status: The new status
        """
        try:
            await self.supabase.table('profile_urls').update({
                'status': status
            }).eq('id', str(url_id)).execute()
            
            logger.info(f"Updated profile URL {url_id} status to {status}")
        
        except Exception as e:
            logger.error(f"Error updating profile URL status: {str(e)}")
            raise
    
    async def store_profile(
        self, job_id: UUID, linkedin_url: str, profile_data: Dict[str, Any],
        job_title: Optional[str] = None, company_specific_title: Optional[str] = None,
        experience_years: Optional[float] = None, meets_criteria: bool = False
    ) -> UUID:
        """
        Store an enriched LinkedIn profile.
        
        Args:
            job_id: The job ID
            linkedin_url: The LinkedIn profile URL
            profile_data: The profile data from ProxyCurl
            job_title: The job title
            company_specific_title: The title at the specific company
            experience_years: The total experience in years
            meets_criteria: Whether the profile meets the job criteria
            
        Returns:
            UUID: The created profile ID
        """
        try:
            result = await self.supabase.table('profiles').insert({
                'job_id': str(job_id),
                'linkedin_url': linkedin_url,
                'profile_data': profile_data,
                'job_title': job_title,
                'company_specific_title': company_specific_title,
                'experience_years': experience_years,
                'meets_criteria': meets_criteria
            }).execute()
            
            profile_id = result.data[0]['id']
            logger.info(f"Stored profile for {linkedin_url} for job {job_id}")
            return UUID(profile_id)
        
        except Exception as e:
            logger.error(f"Error storing profile: {str(e)}")
            raise
    
    async def get_job_progress(self, job_id: UUID) -> JobProgressStats:
        """
        Get progress statistics for a job.
        
        Args:
            job_id: The job ID
            
        Returns:
            JobProgressStats: The job progress statistics
        """
        try:
            # Get search query stats
            search_query_stats = await self.supabase.rpc(
                'get_search_query_stats',
                {'job_uuid': str(job_id)}
            ).execute()
            
            # Get profile stats
            profile_stats = await self.supabase.rpc(
                'get_profile_stats',
                {'job_uuid': str(job_id)}
            ).execute()
            
            # Extract data from results
            searches_total = search_query_stats.data[0]['total'] if search_query_stats.data else 0
            searches_completed = search_query_stats.data[0]['completed'] if search_query_stats.data else 0
            profiles_discovered = profile_stats.data[0]['discovered'] if profile_stats.data else 0
            profiles_enriched = profile_stats.data[0]['enriched'] if profile_stats.data else 0
            
            return JobProgressStats(
                searches_completed=searches_completed,
                searches_total=searches_total,
                profiles_discovered=profiles_discovered,
                profiles_enriched=profiles_enriched
            )
        
        except Exception as e:
            logger.error(f"Error getting job progress: {str(e)}")
            raise
    
    async def get_profile_urls(self, job_id: UUID) -> List[ProfileUrl]:
        """
        Get all profile URLs for a job.
        
        Args:
            job_id: The job ID
            
        Returns:
            List[ProfileUrl]: The profile URLs
        """
        try:
            result = await self.supabase.table('profile_urls').select('*').eq('job_id', str(job_id)).execute()
            
            return [ProfileUrl(**item) for item in result.data]
        
        except Exception as e:
            logger.error(f"Error getting profile URLs: {str(e)}")
            raise
    
    async def get_job_titles(self, job_id: UUID) -> List[TitleCount]:
        """
        Get grouped job titles for a job.
        
        Args:
            job_id: The job ID
            
        Returns:
            List[TitleCount]: The job title counts
        """
        try:
            # Get titles from database
            result = await self.supabase.rpc(
                'aggregate_job_titles',
                {'job_uuid': str(job_id)}
            ).execute()
            
            # Get selected titles
            selected_result = await self.supabase.table('title_selections').select('company', 'title', 'selected').eq('job_id', str(job_id)).execute()
            
            # Create mapping of selected titles
            selected_map = {
                f"{item['company']}:{item['title']}": item['selected']
                for item in selected_result.data
            }
            
            # Create title counts
            title_counts = [
                TitleCount(
                    company=item['company'],
                    title=item['title'],
                    count=item['count'],
                    selected=selected_map.get(f"{item['company']}:{item['title']}", False)
                )
                for item in result.data
            ]
            
            return title_counts
        
        except Exception as e:
            logger.error(f"Error getting job titles: {str(e)}")
            raise
    
    async def update_title_selections(self, job_id: UUID, titles: List[TitleCount]) -> None:
        """
        Update title selections for a job.
        
        Args:
            job_id: The job ID
            titles: The title selections
        """
        try:
            # Clear existing selections
            await self.supabase.table('title_selections').delete().eq('job_id', str(job_id)).execute()
            
            # Insert new selections
            title_data = [
                {
                    'job_id': str(job_id),
                    'company': title.company,
                    'title': title.title,
                    'count': title.count,
                    'selected': title.selected
                }
                for title in titles
            ]
            
            if title_data:
                await self.supabase.table('title_selections').insert(title_data).execute()
            
            logger.info(f"Updated title selections for job {job_id}")
        
        except Exception as e:
            logger.error(f"Error updating title selections: {str(e)}")
            raise
    
    async def create_export(self, job_id: UUID) -> UUID:
        """
        Create a new export for a job.
        
        Args:
            job_id: The job ID
            
        Returns:
            UUID: The created export ID
        """
        try:
            result = await self.supabase.table('exports').insert({
                'job_id': str(job_id),
                'status': 'pending',
                'profiles_exported': 0
            }).execute()
            
            export_id = result.data[0]['id']
            logger.info(f"Created export for job {job_id}")
            return UUID(export_id)
        
        except Exception as e:
            logger.error(f"Error creating export: {str(e)}")
            raise
    
    async def update_export(
        self, export_id: UUID, status: str, 
        google_sheet_url: Optional[str] = None,
        profiles_exported: Optional[int] = None,
        completed_at: Optional[str] = None
    ) -> None:
        """
        Update an export.
        
        Args:
            export_id: The export ID
            status: The new status
            google_sheet_url: The Google Sheet URL
            profiles_exported: The number of profiles exported
            completed_at: The completion timestamp
        """
        try:
            update_data = {'status': status}
            
            if google_sheet_url:
                update_data['google_sheet_url'] = google_sheet_url
            
            if profiles_exported is not None:
                update_data['profiles_exported'] = profiles_exported
            
            if completed_at:
                update_data['completed_at'] = completed_at
            
            await self.supabase.table('exports').update(update_data).eq('id', str(export_id)).execute()
            logger.info(f"Updated export {export_id} status to {status}")
        
        except Exception as e:
            logger.error(f"Error updating export: {str(e)}")
            raise
    
    async def get_export(self, job_id: UUID) -> Optional[Export]:
        """
        Get the most recent export for a job.
        
        Args:
            job_id: The job ID
            
        Returns:
            Optional[Export]: The export details or None if not found
        """
        try:
            result = await self.supabase.table('exports').select('*').eq('job_id', str(job_id)).order('created_at', desc=True).limit(1).execute()
            
            if not result.data:
                return None
            
            return Export(**result.data[0])
        
        except Exception as e:
            logger.error(f"Error getting export for job {job_id}: {str(e)}")
            raise
    
    async def get_selected_profiles(self, job_id: UUID) -> List[Profile]:
        """
        Get profiles for selected job titles.
        
        Args:
            job_id: The job ID
            
        Returns:
            List[Profile]: The selected profiles
        """
        try:
            # Get selected titles
            title_result = await self.supabase.table('title_selections').select('company', 'title').eq('job_id', str(job_id)).eq('selected', True).execute()
            
            if not title_result.data:
                return []
            
            # Create title filter conditions
            title_conditions = [
                f"(company = '{title['company']}' AND job_title = '{title['title']}')"
                for title in title_result.data
            ]
            
            # Get profiles matching selected titles
            profile_result = await self.supabase.rpc(
                'get_profiles_by_titles',
                {
                    'job_uuid': str(job_id),
                    'title_filter': ' OR '.join(title_conditions)
                }
            ).execute()
            
            return [Profile(**profile) for profile in profile_result.data]
        
        except Exception as e:
            logger.error(f"Error getting selected profiles: {str(e)}")
            raise
