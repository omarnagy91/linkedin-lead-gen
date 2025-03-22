import datetime
import logging
import re
from typing import Dict, List, Optional, Tuple, Union

import httpx
from dateutil.relativedelta import relativedelta
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.api import EnrichmentResult
from app.utils.config import settings

logger = logging.getLogger(__name__)

# Seniority level regex pattern
SENIORITY_PATTERN = r'(?i)\b(?:partner|director|manager|cxo|owner|vice\s*president|chief|c.o|ceo|cto|cfo|coo|president)\b'


class ProxyCurlService:
    """Service for LinkedIn profile and company enrichment via ProxyCurl API"""
    
    def __init__(self):
        self.api_key = settings.PROXYCURL_API_KEY
        self.person_url = "https://nubela.co/proxycurl/api/v2/linkedin"
        self.company_url = "https://nubela.co/proxycurl/api/linkedin/company"
        self.timeout = settings.REQUEST_TIMEOUT
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_company_profile(self, linkedin_url: str) -> Tuple[bool, Dict]:
        """
        Get LinkedIn company profile using ProxyCurl API.
        
        Args:
            linkedin_url: The LinkedIn company URL
            
        Returns:
            Tuple[bool, Dict]: Success flag and company data or error message
        """
        logger.info(f"Getting company profile: {linkedin_url}")
        
        params = {
            'url': linkedin_url,
            'use_cache': 'if-present',  # Use cache if available
            'fallback_to_cache': 'on-error',  # Fallback to cache on error
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.company_url, params=params, headers=headers)
                
                if response.status_code == 200:
                    company_data = response.json()
                    logger.info(f"Successfully got company profile: {linkedin_url}")
                    return True, company_data
                else:
                    error_message = f"ProxyCurl API error: {response.status_code} - {response.text}"
                    logger.error(error_message)
                    return False, {"error": error_message}
        
        except Exception as e:
            error_message = f"Error getting company profile: {str(e)}"
            logger.error(error_message)
            return False, {"error": error_message}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def enrich_profile(
        self, linkedin_url: str, company_name: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        Enrich a LinkedIn profile using ProxyCurl API.
        
        Args:
            linkedin_url: The LinkedIn profile URL
            company_name: Optional company name for filtering
            
        Returns:
            Tuple[bool, Dict]: Success flag and profile data or error message
        """
        logger.info(f"Enriching profile: {linkedin_url}")
        
        params = {
            'linkedin_profile_url': linkedin_url,
            'use_cache': 'if-present',  # Use cache if available
            'fallback_to_cache': 'on-error',  # Fallback to cache on error
            'skills': 'include',
            'experiences': 'include',
            'education': 'include'
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.person_url, params=params, headers=headers)
                
                if response.status_code == 200:
                    profile_data = response.json()
                    logger.info(f"Successfully enriched profile: {linkedin_url}")
                    return True, profile_data
                else:
                    error_message = f"ProxyCurl API error: {response.status_code} - {response.text}"
                    logger.error(error_message)
                    return False, {"error": error_message}
        
        except Exception as e:
            error_message = f"Error enriching profile: {str(e)}"
            logger.error(error_message)
            return False, {"error": error_message}
    
    @staticmethod
    def extract_current_title(profile_data: Dict) -> Optional[str]:
        """
        Extract the current job title from a profile.
        
        Args:
            profile_data: The profile data from ProxyCurl
            
        Returns:
            Optional[str]: The current job title or None
        """
        experiences = profile_data.get("experiences", [])
        
        # Filter for current positions (no end date)
        current_positions = [
            exp for exp in experiences
            if not exp.get("ends_at")
        ]
        
        if current_positions:
            # Sort by start date (most recent first)
            sorted_positions = sorted(
                current_positions,
                key=lambda x: (
                    x.get("starts_at", {}).get("year", 0),
                    x.get("starts_at", {}).get("month", 0)
                ),
                reverse=True
            )
            
            # Return the title of the most recent position
            return sorted_positions[0].get("title")
        
        return None
    
    @staticmethod
    def extract_title_at_company(
        profile_data: Dict, company_name: str, employment_status: str = "all"
    ) -> Optional[str]:
        """
        Extract the job title at a specific company.
        
        Args:
            profile_data: The profile data from ProxyCurl
            company_name: The company name to look for
            employment_status: Whether to look for current, past, or all positions
            
        Returns:
            Optional[str]: The job title at the company or None
        """
        experiences = profile_data.get("experiences", [])
        
        # Normalize company name for comparison
        normalized_company = company_name.lower()
        
        # Filter experiences by company
        company_experiences = []
        
        for exp in experiences:
            exp_company = exp.get("company", "").lower()
            
            # Skip if no company match
            if normalized_company not in exp_company:
                continue
            
            # Check employment status filter
            if employment_status == "current" and exp.get("ends_at"):
                continue
            elif employment_status == "past" and not exp.get("ends_at"):
                continue
            
            # For past employees, check if they left within 5 years
            if employment_status in ["past", "all"] and exp.get("ends_at"):
                end_year = exp.get("ends_at", {}).get("year")
                end_month = exp.get("ends_at", {}).get("month", 1)
                
                if end_year:
                    end_date = datetime.datetime(end_year, end_month, 1)
                    cutoff_date = datetime.datetime.now() - relativedelta(years=5)
                    
                    if end_date < cutoff_date:
                        continue
            
            company_experiences.append(exp)
        
        if company_experiences:
            # Sort by start date (most recent first)
            sorted_experiences = sorted(
                company_experiences,
                key=lambda x: (
                    x.get("starts_at", {}).get("year", 0),
                    x.get("starts_at", {}).get("month", 0)
                ),
                reverse=True
            )
            
            # Return the title of the most recent position
            return sorted_experiences[0].get("title")
        
        return None
    
    @staticmethod
    def calculate_experience_years(profile_data: Dict) -> float:
        """
        Calculate total professional experience in years.
        
        Args:
            profile_data: The profile data from ProxyCurl
            
        Returns:
            float: Total professional experience in years
        """
        experiences = profile_data.get("experiences", [])
        if not experiences:
            return 0.0
        
        # Sort experiences by start date
        sorted_experiences = sorted(
            experiences, 
            key=lambda x: (
                x.get("starts_at", {}).get("year", 9999),
                x.get("starts_at", {}).get("month", 12)
            )
        )
        
        # Calculate total duration considering overlaps
        total_days = 0
        current_period = None
        
        for exp in sorted_experiences:
            # Get start date
            start_year = exp.get("starts_at", {}).get("year")
            start_month = exp.get("starts_at", {}).get("month", 1)
            
            if not start_year:
                continue
            
            # Get end date (use current date if still working)
            end_data = exp.get("ends_at")
            if not end_data:
                end_year = datetime.datetime.now().year
                end_month = datetime.datetime.now().month
            else:
                end_year = end_data.get("year")
                end_month = end_data.get("month", 12)
                
                if not end_year:
                    end_year = datetime.datetime.now().year
                    end_month = datetime.datetime.now().month
            
            # Create dates
            start_date = datetime.datetime(start_year, start_month, 1)
            end_date = datetime.datetime(end_year, end_month, 28)
            
            # Handle period merging for overlapping experiences
            if current_period:
                current_start, current_end = current_period
                
                # Check for overlap
                if start_date <= current_end:
                    # Extend current period if this experience ends later
                    if end_date > current_end:
                        current_period = (current_start, end_date)
                else:
                    # No overlap, add previous period to total
                    days = (current_end - current_start).days
                    total_days += days
                    current_period = (start_date, end_date)
            else:
                current_period = (start_date, end_date)
        
        # Add final period
        if current_period:
            days = (current_period[1] - current_period[0]).days
            total_days += days
        
        # Convert days to years
        total_years = total_days / 365.25
        
        return round(total_years, 1)
    
    @staticmethod
    def check_profile_criteria(
        profile_data: Dict, employment_status: str = "all"
    ) -> bool:
        """
        Check if a profile meets the job criteria.
        
        Args:
            profile_data: The profile data from ProxyCurl
            employment_status: Whether to check criteria for current, past, or all positions
            
        Returns:
            bool: True if the profile meets criteria, False otherwise
        """
        # Check experience criteria
        experience_years = ProxyCurlService.calculate_experience_years(profile_data)
        
        if employment_status == "current" and experience_years < 6.0:
            return False
        elif employment_status == "past" and experience_years < 10.0:
            return False
        elif employment_status == "all":
            # For 'all', check if either current or past criteria met
            current_title = ProxyCurlService.extract_current_title(profile_data)
            
            if current_title:
                # Current employee - need 6+ years
                if experience_years < 6.0:
                    return False
            else:
                # Past employee - need 10+ years
                if experience_years < 10.0:
                    return False
        
        # Check seniority criteria
        job_title = profile_data.get("headline", "")
        
        if not job_title:
            current_exp = next((exp for exp in profile_data.get("experiences", []) 
                               if not exp.get("ends_at")), None)
            if current_exp:
                job_title = current_exp.get("title", "")
        
        if not job_title:
            return False
        
        # Check if job title contains seniority keywords
        return bool(re.search(SENIORITY_PATTERN, job_title))
    
    @staticmethod
    def check_past_employee_criteria(profile_data: Dict, company_name: str) -> bool:
        """
        Check if a past employee meets specific criteria.
        
        Args:
            profile_data: The profile data from ProxyCurl
            company_name: The company name to check
            
        Returns:
            bool: True if criteria met, False otherwise
        """
        # Normalize company name for comparison
        normalized_company = company_name.lower()
        
        # Find company experience
        company_exp = None
        for exp in profile_data.get("experiences", []):
            exp_company = exp.get("company", "").lower()
            
            if normalized_company in exp_company and exp.get("ends_at"):
                company_exp = exp
                break
        
        if not company_exp:
            return False
        
        # Check if left within last 5 years
        end_year = company_exp.get("ends_at", {}).get("year")
        end_month = company_exp.get("ends_at", {}).get("month", 1)
        
        if not end_year:
            return False
        
        end_date = datetime.datetime(end_year, end_month, 1)
        cutoff_date = datetime.datetime.now() - relativedelta(years=5)
        
        if end_date < cutoff_date:
            return False
        
        # Check total experience
        experience_years = ProxyCurlService.calculate_experience_years(profile_data)
        if experience_years < 10.0:
            return False
        
        # Check seniority in role at the company
        job_title = company_exp.get("title", "")
        return bool(re.search(SENIORITY_PATTERN, job_title))
