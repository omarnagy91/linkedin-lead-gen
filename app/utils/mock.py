import json
import logging
import os
import random
from typing import Dict, List, Optional, Tuple, Union

from app.utils.config import settings

logger = logging.getLogger(__name__)


class MockUtils:
    """Utilities for mock data handling"""
    
    @staticmethod
    def load_mock_search_results(query: str) -> List[Dict]:
        """
        Load mock search results from a file.
        
        Args:
            query: The search query
            
        Returns:
            List[Dict]: List of mock search results
        """
        try:
            search_dir = os.path.join(settings.MOCK_DATA_DIR, "searches")
            
            # List all search result files
            files = os.listdir(search_dir)
            
            if not files:
                logger.warning("No mock search files found")
                return []
            
            # Select a random file for this query
            random_file = random.choice(files)
            file_path = os.path.join(search_dir, random_file)
            
            # Load the file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Return results with some randomization
            results = []
            for result in data.get("results", [])[:20]:  # Take up to 20 results
                if random.random() > 0.2:  # 80% chance to include each result
                    results.append(result)
            
            logger.info(f"Loaded {len(results)} mock search results")
            return results
            
        except Exception as e:
            logger.error(f"Error loading mock search results: {str(e)}")
            return []
    
    @staticmethod
    def load_mock_company_profile(company_url: str) -> Tuple[bool, Dict]:
        """
        Load mock company profile data.
        
        Args:
            company_url: The company LinkedIn URL
            
        Returns:
            Tuple[bool, Dict]: Success flag and company data
        """
        try:
            # Extract company name from URL
            company_name = company_url.split('company/')[1].split('/')[0]
            
            # Create file path for this company
            file_path = os.path.join(settings.MOCK_DATA_DIR, "companies", f"{company_name}.json")
            
            # If mock file exists, use it
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded mock company profile for {company_name}")
                return True, data
            
            # Otherwise generate mock data
            logger.info(f"Generating mock company profile for {company_name}")
            data = {
                "name": company_name.capitalize().replace('-', ' '),
                "description": f"This is a mock description for {company_name}",
                "industry": random.choice(["Software", "Finance", "Healthcare", "Manufacturing", "Retail"]),
                "company_size": [random.randint(50, 500), random.randint(500, 5000)],
                "company_type": random.choice(["PUBLIC_COMPANY", "PRIVATELY_HELD", "SELF_OWNED"]),
                "specialities": ["Technology", "Innovation", "Leadership"],
                "hq": {
                    "city": random.choice(["New York", "San Francisco", "London", "Berlin"]),
                    "country": random.choice(["US", "UK", "DE"]),
                    "state": random.choice(["NY", "CA", "TX"])
                },
                "profile_pic_url": "https://example.com/company.jpg"
            }
            
            # Save for future use
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True, data
            
        except Exception as e:
            logger.error(f"Error loading mock company profile: {str(e)}")
            return False, {"error": str(e)}
    
    @staticmethod
    def load_mock_profile(linkedin_url: str) -> Tuple[bool, Dict]:
        """
        Load mock LinkedIn profile data.
        
        Args:
            linkedin_url: The LinkedIn profile URL
            
        Returns:
            Tuple[bool, Dict]: Success flag and profile data
        """
        try:
            # Extract profile ID from URL
            profile_id = linkedin_url.split('/in/')[1].split('/')[0]
            
            # Create file path for this profile
            file_path = os.path.join(settings.MOCK_DATA_DIR, "profiles", f"{profile_id}.json")
            
            # If mock file exists, use it
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded mock profile for {profile_id}")
                return True, data
            
            # Otherwise generate mock data
            logger.info(f"Generating mock profile for {profile_id}")
            
            # Generate realistic first and last names
            first_names = ["John", "Sarah", "Michael", "Emily", "David", "Jennifer", "Robert", "Linda", "William", "Elizabeth"]
            last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor"]
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            # Generate realistic job title based on seniority
            seniorities = ["Director", "Vice President", "Chief", "Head", "Manager", "Partner"]
            departments = ["Marketing", "Sales", "Engineering", "Product", "Operations", "Finance", "HR", "Technology"]
            seniority = random.choice(seniorities)
            department = random.choice(departments)
            
            if seniority == "Chief":
                job_title = f"Chief {department[:3].upper()}O"  # CEO, CTO, CFO, etc.
            else:
                job_title = f"{seniority} of {department}"
            
            # Generate experience details
            experiences = []
            current_year = 2025
            total_years = random.randint(6, 20)  # Between 6 and 20 years of experience
            
            for i in range(random.randint(2, 5)):  # 2-5 previous jobs
                duration = random.randint(1, 5)  # 1-5 years at each job
                end_year = current_year - sum(random.randint(1, 3) for _ in range(i))
                start_year = end_year - duration
                
                experiences.append({
                    "company": f"Company {i+1}",
                    "title": f"Job Title {i+1}",
                    "starts_at": {"year": start_year, "month": random.randint(1, 12)},
                    "ends_at": {"year": end_year, "month": random.randint(1, 12)} if i > 0 else None
                })
            
            # Sort experiences with most recent first
            experiences.sort(key=lambda x: x["starts_at"]["year"] if x["starts_at"] else 0, reverse=True)
            
            # Create the full profile
            data = {
                "full_name": f"{first_name} {last_name}",
                "first_name": first_name,
                "last_name": last_name,
                "headline": job_title,
                "location": {
                    "country": random.choice(["US", "UK", "DE", "FR", "AU"]),
                    "city": random.choice(["New York", "London", "Berlin", "Paris", "Sydney"])
                },
                "profile_pic_url": "https://example.com/profile.jpg",
                "industry": random.choice(["Software", "Finance", "Healthcare", "Manufacturing", "Retail"]),
                "experiences": experiences,
                "education": [
                    {
                        "school": "University of Example",
                        "degree_name": "Bachelor's Degree",
                        "field_of_study": "Computer Science",
                        "starts_at": {"year": current_year - total_years - 4, "month": 9},
                        "ends_at": {"year": current_year - total_years, "month": 6}
                    }
                ],
                "skills": ["Leadership", "Management", "Strategy", "Innovation"],
                "connections": random.randint(500, 5000)
            }
            
            # Save for future use
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True, data
            
        except Exception as e:
            logger.error(f"Error loading mock profile: {str(e)}")
            return False, {"error": str(e)}
