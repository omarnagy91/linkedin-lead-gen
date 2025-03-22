import json
import logging
import random
from typing import Dict, List

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.utils.config import settings
from app.utils.mock import MockUtils

logger = logging.getLogger(__name__)

# Configure OpenAI API key
openai.api_key = settings.OPENAI_API_KEY


class GPTService:
    """Service for GPT-4 integration"""
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_search_strategies(
        self, company_urls: List[str], countries: List[str], 
        employment_status: str, campaign_goal: str = None,
        company_contexts: List[Dict] = None
    ) -> List[Dict[str, str]]:
        """
        Generate search strategies using GPT-4.
        
        Args:
            company_urls: List of company LinkedIn URLs
            countries: List of target countries
            employment_status: Whether to target current, past, or all employees
            campaign_goal: Optional description of the campaign goal
        
        Returns:
            List[Dict[str, str]]: List of search queries with company and country
        """
        logger.info(f"Generating search strategies for {len(company_urls)} companies in {len(countries)} countries")
        
        # Check if mock mode is enabled
        if settings.MOCK_MODE:
            logger.info("Using mock search strategies")
            
            # Generate mock strategies for each company and country
            strategies = []
            
            for company_url in company_urls:
                # Extract company name from URL
                company_name = company_url.split('company/')[1].split('/')[0].replace('-', ' ').title()
                
                for country in countries:
                    # Generate 2 strategies per company-country combination
                    for i in range(2):
                        job_titles = ["Director", "VP", "Chief", "Manager", "Partner", "Owner", "President"]
                        departments = ["Marketing", "Sales", "Engineering", "Product", "Operations", "Finance"]
                        
                        if i == 0:
                            title = random.choice(job_titles)
                            query = f"site:linkedin.com/in/ {company_name} {title} {country} profile"
                        else:
                            title = random.choice(job_titles)
                            dept = random.choice(departments)
                            query = f"site:linkedin.com/in/ {company_name} {title} of {dept} {country} profile"
                        
                        strategies.append({
                            "company": company_name,
                            "company_url": company_url,
                            "country": country,
                            "query": query
                        })
            
            return strategies
        
        # Real API call
        try:
            # Create company context for better prompting
            company_info = []
            
            if company_contexts:
                # Use provided company contexts
                for context in company_contexts:
                    company_info.append({
                        "name": context.get("name", ""),
                        "url": context.get("url", ""),
                        "industry": context.get("industry", ""),
                        "size": context.get("size", [0, 0]),
                        "description": context.get("description", ""),
                        "specialities": context.get("specialities", [])
                    })
            else:
                # Extract company names from URLs for basic context
                for url in company_urls:
                    company_name = url.split('company/')[1].split('/')[0]
                    company_info.append({
                        "name": company_name,
                        "url": url,
                        "industry": "",
                        "size": [0, 0],
                        "description": "",
                        "specialities": []
                    })
            
            # Create prompt based on employment status
            status_text = {
                "current": "currently working at",
                "past": "previously worked at (within the last 5 years)",
                "all": "currently working at or previously worked at (within the last 5 years)"
            }.get(employment_status, "working at")
            
            experience_text = {
                "current": "with 6-10 years or more of total professional experience",
                "past": "with at least 10 years of total professional experience",
                "all": "with appropriate experience (current: 6-10+ years, former: 10+ years)"
            }.get(employment_status, "with significant experience")
            
            seniority_text = "at the level of partner, director, manager, CXO, owner, or vice president"
            
            # Build company context section
            company_context_text = ""
            for company in company_info:
                company_context_text += f"\nCompany: {company['name']}\n"
                if company["industry"]:
                    company_context_text += f"Industry: {company['industry']}\n"
                if company["description"]:
                    company_context_text += f"Description: {company['description']}\n"
                if company["specialities"]:
                    company_context_text += f"Specialties: {', '.join(company['specialities'])}\n"
            
            # Build prompt for GPT-4
            prompt = f"""
            Generate optimal LinkedIn search queries for finding professionals who are {status_text} the following companies:
            
            {company_context_text}
            
            Target professionals {experience_text} and {seniority_text}.
            
            For each company, create search queries for the following countries: {', '.join(countries)}.
            
            {"The campaign goal is: " + campaign_goal if campaign_goal else ""}
            
            Format your response as a valid JSON array with objects containing:
            1. "company": The company name
            2. "country": The target country
            3. "query": The optimized search query for Google
            
            Focus on creating queries that will find LinkedIn profile URLs. Make sure each query includes:
            - The company name
            - Terms like "LinkedIn profile"
            - Relevant title/position keywords (use industry-specific titles when possible)
            - Country or location information
            - Experience indicators when possible
            
            Generate at least 2 unique queries per company-country combination to maximize coverage.
            """
            
            # Make API call to GPT-4
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-0613",  # Ensure this is the correct model name for your account
                messages=[
                    {"role": "system", "content": "You are a search optimization expert specializing in finding LinkedIn profiles. Your task is to generate optimized search queries to find specific LinkedIn profiles based on given criteria."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            # Extract and parse response
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from the response (in case GPT includes explanatory text)
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = result_text[json_start:json_end]
                search_strategies = json.loads(json_text)
            else:
                # Fallback if clean JSON not found
                search_strategies = []
                logger.warning("Could not extract clean JSON from GPT response")
            
            # Sanity check and mapping company URLs to strategies
            final_strategies = []
            company_url_mapping = dict(zip(company_names, company_urls))
            
            for strategy in search_strategies:
                company_name = strategy.get("company", "")
                country = strategy.get("country", "")
                query = strategy.get("query", "")
                
                # Skip invalid entries
                if not all([company_name, country, query]):
                    continue
                
                # Find matching company URL
                company_url = None
                for name, url in company_url_mapping.items():
                    if name.lower() in company_name.lower() or company_name.lower() in name.lower():
                        company_url = url
                        break
                
                if not company_url:
                    logger.warning(f"Could not match company name {company_name} to URL")
                    continue
                
                # Add to final strategies
                final_strategies.append({
                    "company": company_name,
                    "company_url": company_url,
                    "country": country,
                    "query": query
                })
            
            logger.info(f"Generated {len(final_strategies)} search strategies")
            return final_strategies
            
        except Exception as e:
            logger.error(f"Error generating search strategies: {str(e)}")
            raise
