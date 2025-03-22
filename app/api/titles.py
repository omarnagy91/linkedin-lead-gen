import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.models.job import TitleList, TitleSelection, TitleSelectionResponse
from app.services import db_service
from app.utils.errors import NotFoundError
from app.workers.export_processor import export_selected_profiles

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{job_id}", response_model=TitleList)
async def get_job_titles(job_id: UUID) -> TitleList:
    """
    Get available job titles for a job.
    
    Args:
        job_id: The job ID
        
    Returns:
        TitleList: List of job titles with counts
    """
    logger.info(f"Getting titles for job {job_id}")
    
    try:
        # Check if job exists
        await db_service.get_job(job_id)
        
        # Get job titles
        titles = await db_service.get_job_titles(job_id)
        
        return TitleList(
            job_id=job_id,
            titles=titles
        )
    
    except ValueError as e:
        logger.error(f"Job not found: {job_id}")
        raise NotFoundError(f"Job not found: {job_id}")
    
    except Exception as e:
        logger.error(f"Error getting job titles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job titles: {str(e)}"
        )


@router.post("/{job_id}", response_model=TitleSelectionResponse)
async def select_job_titles(
    job_id: UUID, title_selection: TitleSelection, background_tasks: BackgroundTasks
) -> TitleSelectionResponse:
    """
    Select job titles for export.
    
    Args:
        job_id: The job ID
        title_selection: The selected titles
        background_tasks: Background tasks handler
        
    Returns:
        TitleSelectionResponse: Response with status
    """
    logger.info(f"Selecting titles for job {job_id}")
    
    try:
        # Check if job exists
        job = await db_service.get_job(job_id)
        
        # Update title selections
        await db_service.update_title_selections(job_id, title_selection.titles)
        
        # Update job status
        await db_service.update_job_status(job_id, "exporting")
        
        # Start export process in background
        background_tasks.add_task(export_selected_profiles, job_id)
        
        return TitleSelectionResponse(
            job_id=job_id,
            status="exporting",
            message="Titles selected successfully, export started"
        )
    
    except ValueError as e:
        logger.error(f"Job not found: {job_id}")
        raise NotFoundError(f"Job not found: {job_id}")
    
    except Exception as e:
        logger.error(f"Error selecting job titles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to select job titles: {str(e)}"
        )
