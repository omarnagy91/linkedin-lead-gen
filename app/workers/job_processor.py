import asyncio
import logging
from datetime import datetime
from uuid import UUID

from app.models.job import JobStatus
from app.services import db_service, gpt_service, proxycurl_service, search_service
from app.utils.logging import get_logger

logger = logging.getLogger(__name__)


async def process_job(job_id: UUID):
    """
    Process a job with parallel search and enrichment.
    
    Args:
        job_id: The job ID to process
    """
    job_logger = get_logger("job_processor", str(job_id))
    job_logger.info(f"Starting job processing")
    
    try:
        # Update job status
        await db_service.update_job_status(job_id, JobStatus.PROCESSING)
        
        # Get job details
        job = await db_service.get_job(job_id)
        
        # Extract company context for better search strategies
        job_logger.info("Extracting company context")
        company_contexts = []
        
        for company_url in job.company_urls:
            # Get company information from ProxyCurl
            success, company_data = await proxycurl_service.get_company_profile(company_url)
            
            if success:
                company_contexts.append({
                    "url": company_url,
                    "name": company_data.get("name", ""),
                    "industry": company_data.get("industry", ""),
                    "size": company_data.get("company_size", [0, 0]),
                    "description": company_data.get("description", ""),
                    "specialities": company_data.get("specialities", [])
                })
            else:
                # If company data fetch fails, still continue with basic info
                company_name = company_url.split("company/")[1].split("/")[0]
                company_contexts.append({
                    "url": company_url,
                    "name": company_name,
                    "industry": "",
                    "size": [0, 0],
                    "description": "",
                    "specialities": []
                })
        
        # Generate search strategies with enhanced context
        job_logger.info("Generating search strategies")
        search_strategies = await gpt_service.generate_search_strategies(
            company_urls=job.company_urls,
            countries=job.countries,
            employment_status=job.employment_status,
            campaign_goal=job.campaign_goal,
            company_contexts=company_contexts
        )
        
        # Store queries in database
        job_logger.info(f"Storing {len(search_strategies)} search queries")
        query_ids = await db_service.store_search_queries(job_id, search_strategies)
        
        # Set up processing queues
        search_queue = asyncio.Queue()
        profile_queue = asyncio.Queue()
        
        # Number of worker tasks
        search_worker_count = min(len(query_ids), 5)  # Max 5 concurrent searches
        
        # Start worker tasks
        job_logger.info(f"Starting {search_worker_count} search workers")
        search_workers = [
            asyncio.create_task(search_worker(search_queue, profile_queue, job_id))
            for _ in range(search_worker_count)
        ]
        
        # Queue up search tasks
        for query_id in query_ids:
            await search_queue.put(query_id)
        
        # Add end markers for workers
        for _ in range(search_worker_count):
            await search_queue.put(None)
        
        # Wait for all searches to complete
        job_logger.info("Waiting for search workers to complete")
        await asyncio.gather(*search_workers)
        
        # Process job titles
        job_logger.info("Extracting and grouping job titles")
        await extract_and_group_job_titles(job_id)
        
        # Update job status
        job_logger.info("Job processing completed, awaiting title selection")
        await db_service.update_job_status(job_id, JobStatus.AWAITING_SELECTION)
    
    except Exception as e:
        job_logger.error(f"Error processing job: {str(e)}", exc_info=True)
        await db_service.update_job_status(job_id, JobStatus.FAILED)


async def search_worker(search_queue, profile_queue, job_id: UUID):
    """
    Worker to process search queries and extract LinkedIn profile URLs.
    
    Args:
        search_queue: Queue of search query IDs to process
        profile_queue: Queue to put discovered profile URLs
        job_id: The job ID
    """
    worker_logger = get_logger("search_worker", str(job_id))
    
    while True:
        # Get next search query from queue
        query_id = await search_queue.get()
        
        # Exit condition
        if query_id is None:
            worker_logger.info("Received exit signal")
            search_queue.task_done()
            break
        
        try:
            # Get query details
            query = await db_service.get_search_query(query_id)
            worker_logger.info(f"Processing query: {query.query}")
            
            # Execute search with SerpAPI
            results = await search_service.execute_search(query.query)
            
            # Process search results
            profile_count = 0
            
            for result in results:
                # Check if URL is a valid LinkedIn profile URL
                if not search_service.validate_linkedin_url(result.url):
                    continue
                
                # Check if URL already exists
                url_exists = await db_service.check_url_exists(query.job_id, result.url)
                
                if not url_exists:
                    # Store new URL
                    await db_service.store_profile_url(
                        job_id=query.job_id,
                        linkedin_url=result.url,
                        company=query.company,
                        country=query.country,
                        search_snippet=result.snippet
                    )
                    
                    profile_count += 1
            
            # Update query status
            await db_service.update_search_query(
                query_id, 
                status="completed", 
                results_count=profile_count
            )
            
            worker_logger.info(f"Completed query with {profile_count} results")
                
        except Exception as e:
            worker_logger.error(f"Error processing search query {query_id}: {str(e)}", exc_info=True)
            await db_service.update_search_query(query_id, status="error")
        
        # Mark task as done
        search_queue.task_done()


async def extract_and_group_job_titles(job_id: UUID):
    """
    Extract and group job titles from profiles.
    
    Args:
        job_id: The job ID
    """
    logger = get_logger("job_titles", str(job_id))
    logger.info("Starting job title extraction")
    
    try:
        # Get job details for filtering criteria
        job = await db_service.get_job(job_id)
        
        # Get profile URLs
        profile_urls = await db_service.get_profile_urls(job_id)
        
        # Enrich profiles in batches
        batch_size = 10
        total_profiles = len(profile_urls)
        processed = 0
        
        for i in range(0, total_profiles, batch_size):
            batch = profile_urls[i:i+batch_size]
            tasks = []
            
            for profile_url in batch:
                task = asyncio.create_task(enrich_profile(
                    job_id=job_id,
                    profile_url=profile_url,
                    employment_status=job.employment_status
                ))
                tasks.append(task)
            
            # Wait for batch to complete
            await asyncio.gather(*tasks)
            
            processed += len(batch)
            logger.info(f"Enriched {processed}/{total_profiles} profiles")
        
        logger.info("Profile enrichment completed")
        
    except Exception as e:
        logger.error(f"Error extracting job titles: {str(e)}", exc_info=True)
        raise


async def enrich_profile(job_id: UUID, profile_url, employment_status: str):
    """
    Enrich a LinkedIn profile with ProxyCurl.
    
    Args:
        job_id: The job ID
        profile_url: The profile URL object
        employment_status: The employment status filter
    """
    logger = get_logger("profile_enrichment", str(job_id))
    
    try:
        # Update profile URL status
        await db_service.update_profile_url_status(profile_url.id, "processing")
        
        # Enrich profile with ProxyCurl
        success, profile_data = await proxycurl_service.enrich_profile(
            linkedin_url=profile_url.linkedin_url,
            company_name=profile_url.company
        )
        
        if not success:
            logger.warning(f"Failed to enrich profile: {profile_url.linkedin_url}")
            await db_service.update_profile_url_status(profile_url.id, "failed")
            return
        
        # Extract job title
        if employment_status == "current":
            job_title = proxycurl_service.extract_current_title(profile_data)
        else:
            job_title = proxycurl_service.extract_title_at_company(
                profile_data, profile_url.company, employment_status
            )
        
        # Calculate experience
        experience_years = proxycurl_service.calculate_experience_years(profile_data)
        
        # Check if profile meets criteria
        meets_criteria = False
        
        if employment_status == "current":
            # Current employees need 6-10+ years experience
            if experience_years >= 6:
                meets_criteria = True
        elif employment_status == "past":
            # Past employees need 10+ years experience and left within 5 years
            if experience_years >= 10 and proxycurl_service.check_past_employee_criteria(
                profile_data, profile_url.company
            ):
                meets_criteria = True
        else:  # "all"
            # Apply criteria based on current status
            is_current = proxycurl_service.extract_current_title(profile_data) is not None
            
            if is_current and experience_years >= 6:
                meets_criteria = True
            elif not is_current and experience_years >= 10 and proxycurl_service.check_past_employee_criteria(
                profile_data, profile_url.company
            ):
                meets_criteria = True
        
        # Check seniority level
        if meets_criteria and job_title:
            meets_criteria = proxycurl_service.check_profile_criteria(profile_data)
        
        # Store profile
        await db_service.store_profile(
            job_id=job_id,
            linkedin_url=profile_url.linkedin_url,
            profile_data=profile_data,
            job_title=job_title,
            company_specific_title=job_title,  # Same as job_title for our use case
            experience_years=experience_years,
            meets_criteria=meets_criteria
        )
        
        # Update profile URL status
        await db_service.update_profile_url_status(profile_url.id, "completed")
        
    except Exception as e:
        logger.error(f"Error enriching profile {profile_url.linkedin_url}: {str(e)}", exc_info=True)
        await db_service.update_profile_url_status(profile_url.id, "error")
