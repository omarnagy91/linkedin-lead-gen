import logging
import re
from typing import List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.api import SearchResult
from app.utils.config import settings
from app.utils.mock import MockUtils

logger = logging.getLogger(__name__)

# LinkedIn profile URL pattern
LINKEDIN_PROFILE_PATTERN = r'linkedin\.com/in/[a-zA-Z0-9\-_%]{5,}'


class SearchService:
    """Service for handling search operations via SerpAPI"""
    
    def __init__(self):
        self.api_key = settings.SERPAPI_API_KEY
        self.base_url = "https://serpapi.com/search"
        self.timeout = settings.REQUEST_TIMEOUT
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def execute_search(self, query: str, num_results: int = 100) -> List[SearchResult]:
        """
        Execute a search using SerpAPI.
        
        Args:
            query: The search query string
            num_results: Number of results to retrieve
            
        Returns:
            List[SearchResult]: List of search results containing LinkedIn profile URLs
        """
        logger.info(f"Executing search: {query}")
        
        # Check if mock mode is enabled
        if settings.MOCK_MODE:
            logger.info("Using mock search results")
            mock_results = MockUtils.load_mock_search_results(query)
            
            # Convert mock results to SearchResult objects
            linkedin_results = []
            for result in mock_results:
                url = result.get("link", "")
                if not url or not self.validate_linkedin_url(url):
                    continue
                    
                linkedin_results.append(
                    SearchResult(
                        title=result.get("title", ""),
                        url=url,
                        snippet=result.get("snippet", "")
                    )
                )
            
            return linkedin_results
            
        # Real API call
        params = {
            "api_key": self.api_key,
            "engine": "google",
            "q": query,
            "num": num_results,
            "gl": "us",  # Google country
            "hl": "en",  # Language
            "no_cache": "true"  # Disable SerpAPI caching for fresh results
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                organic_results = data.get("organic_results", [])
                
                # Process results to extract LinkedIn profile URLs
                linkedin_results = []
                
                for result in organic_results:
                    # Skip results that clearly won't contain LinkedIn profiles
                    if "linkedin.com/company/" in result.get("link", ""):
                        continue
                    
                    # Check for LinkedIn profile URL in the link
                    link = result.get("link", "")
                    if re.search(LINKEDIN_PROFILE_PATTERN, link):
                        linkedin_results.append(
                            SearchResult(
                                title=result.get("title", ""),
                                url=link,
                                snippet=result.get("snippet", "")
                            )
                        )
                        continue
                    
                    # Check for LinkedIn profile URL in the snippet
                    snippet = result.get("snippet", "")
                    profile_match = re.search(LINKEDIN_PROFILE_PATTERN, snippet)
                    if profile_match:
                        # Extract the full URL
                        start_pos = profile_match.start()
                        # Find the start of the URL (could be https:// or just linkedin.com)
                        url_start = max(0, snippet.rfind("https://", 0, start_pos))
                        if url_start == -1:
                            url_start = max(0, snippet.rfind("http://", 0, start_pos))
                        if url_start == -1:
                            url_start = max(0, snippet.rfind("www.", 0, start_pos))
                        if url_start == -1:
                            url_start = start_pos
                        
                        # Find the end of the URL
                        url_end = snippet.find(" ", start_pos)
                        if url_end == -1:
                            url_end = len(snippet)
                        
                        # Extract and normalize the URL
                        profile_url = snippet[url_start:url_end].strip()
                        if not profile_url.startswith(("http://", "https://")):
                            profile_url = "https://" + profile_url
                        
                        linkedin_results.append(
                            SearchResult(
                                title=result.get("title", ""),
                                url=profile_url,
                                snippet=snippet
                            )
                        )
                
                # Log the results
                logger.info(f"Found {len(linkedin_results)} LinkedIn profile URLs")
                return linkedin_results
                
        except Exception as e:
            logger.error(f"Error executing search: {str(e)}")
            raise
    
    @staticmethod
    def validate_linkedin_url(url: str) -> bool:
        """
        Validate that a URL is a LinkedIn profile URL.
        
        Args:
            url: The URL to validate
            
        Returns:
            bool: True if the URL is a valid LinkedIn profile URL
        """
        return bool(re.search(LINKEDIN_PROFILE_PATTERN, url))
    
    @staticmethod
    def extract_linkedin_username(url: str) -> Optional[str]:
        """
        Extract the LinkedIn username from a profile URL.
        
        Args:
            url: The LinkedIn profile URL
            
        Returns:
            Optional[str]: The LinkedIn username or None if not found
        """
        match = re.search(LINKEDIN_PROFILE_PATTERN, url)
        if match:
            # Extract the username part
            full_path = url[match.start():]
            username_part = full_path.split("/in/")[1]
            # Clean up any trailing parameters or slashes
            username = username_part.split("/")[0].split("?")[0]
            return username
        return None
