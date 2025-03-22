import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.models.job import ExportStatus
from app.services import db_service
from app.utils.errors import NotFoundError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{job_id}", response_model=ExportStatus)
async def get_export_status(job_id: UUID) -> ExportStatus:
    """
    Get the status of an export.
    
    Args:
        job_id: The job ID
        
    Returns:
        ExportStatus: The export status
    """
    logger.info(f"Getting export status for job {job_id}")
    
    try:
        # Check if job exists
        job = await db_service.get_job(job_id)
        
        # Get export
        export = await db_service.get_export(job_id)
        
        if not export:
            return ExportStatus(
                job_id=job_id,
                status="not_started",
                profiles_exported=0
            )
        
        return ExportStatus(
            job_id=job_id,
            status=export.status,
            export_url=export.google_sheet_url,
            profiles_exported=export.profiles_exported,
            completed_at=export.completed_at
        )
    
    except ValueError as e:
        logger.error(f"Job not found: {job_id}")
        raise NotFoundError(f"Job not found: {job_id}")
    
    except Exception as e:
        logger.error(f"Error getting export status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export status: {str(e)}"
        )
