import logging
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.models.job import (
    JobCreate, 
    JobProgressStats, 
    JobResponse, 
    JobStatus as JobStatusModel
)
from app.services import db_service
from app.utils.errors import NotFoundError
from app.workers.job_processor import process_job

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate, background_tasks: BackgroundTasks) -> JobResponse:
    """
    Create a new LinkedIn lead generation job.
    
    Args:
        job_data: The job creation data
        background_tasks: Background tasks handler
        
    Returns:
        JobResponse: The created job details
    """
    logger.info(f"Creating job for {job_data.user_email}")
    
    try:
        # Create job in database
        job_id = await db_service.create_job(job_data)
        
        # Start processing job in background
        background_tasks.add_task(process_job, job_id)
        
        return JobResponse(
            job_id=job_id,
            status="processing",
            message="Job created successfully"
        )
    
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/{job_id}", response_model=JobStatusModel)
async def get_job_status(job_id: UUID) -> JobStatusModel:
    """
    Get the status of a job.
    
    Args:
        job_id: The job ID
        
    Returns:
        JobStatusModel: The job status
    """
    logger.info(f"Getting status for job {job_id}")
    
    try:
        # Get job from database
        job = await db_service.get_job(job_id)
        
        # Get job progress
        progress = await db_service.get_job_progress(job_id)
        
        return JobStatusModel(
            job_id=job_id,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at,
            progress=progress
        )
    
    except ValueError as e:
        logger.error(f"Job not found: {job_id}")
        raise NotFoundError(f"Job not found: {job_id}")
    
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )
