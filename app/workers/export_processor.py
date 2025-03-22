import logging
from datetime import datetime
from uuid import UUID

from app.models.job import JobStatus
from app.services import db_service, sheets_service
from app.utils.logging import get_logger

logger = logging.getLogger(__name__)


async def export_selected_profiles(job_id: UUID):
    """
    Export selected profiles to Google Sheets.
    
    Args:
        job_id: The job ID
    """
    job_logger = get_logger("export_processor", str(job_id))
    job_logger.info(f"Starting export process")
    
    try:
        # Update job status
        await db_service.update_job_status(job_id, JobStatus.EXPORTING)
        
        # Get job details
        job = await db_service.get_job(job_id)
        
        # Create export record
        export_id = await db_service.create_export(job_id)
        
        # Get selected profiles
        profiles = await db_service.get_selected_profiles(job_id)
        
        if not profiles:
            job_logger.warning("No profiles selected for export")
            await db_service.update_export(
                export_id=export_id,
                status="completed",
                profiles_exported=0,
                completed_at=datetime.now().isoformat()
            )
            await db_service.update_job_status(job_id, JobStatus.COMPLETED)
            return
        
        # Generate sheet name
        sheet_name = f"Leads_{job.user_email.split('@')[0]}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        # Export to Google Sheets
        job_logger.info(f"Exporting {len(profiles)} profiles to sheet: {sheet_name}")
        profiles_exported = await sheets_service.export_profiles(profiles, sheet_name)
        
        # Get sheet URL
        sheet_url = await sheets_service.get_sheet_url(sheet_name)
        
        # Update export status
        await db_service.update_export(
            export_id=export_id,
            status="completed",
            google_sheet_url=sheet_url,
            profiles_exported=profiles_exported,
            completed_at=datetime.now().isoformat()
        )
        
        # Update job status
        await db_service.update_job_status(job_id, JobStatus.COMPLETED)
        
        job_logger.info(f"Export completed: {profiles_exported} profiles exported")
        
    except Exception as e:
        job_logger.error(f"Error exporting profiles: {str(e)}", exc_info=True)
        
        # Update export status if export record exists
        try:
            export = await db_service.get_export(job_id)
            if export:
                await db_service.update_export(
                    export_id=export.id,
                    status="failed",
                    completed_at=datetime.now().isoformat()
                )
        except Exception:
            pass
        
        # Update job status
        await db_service.update_job_status(job_id, JobStatus.FAILED)
