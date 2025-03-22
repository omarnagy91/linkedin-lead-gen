import logging
from typing import Dict

from fastapi import APIRouter, HTTPException, status

from app.services import db_service
from app.utils.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("")
async def health_check() -> Dict[str, str]:
    """
    Check the health of the API.
    
    Returns:
        Dict[str, str]: Health status
    """
    logger.info("Health check requested")
    
    try:
        # Check database connection
        db_health = "healthy"
        
        try:
            await db_service.supabase.health().execute()
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            db_health = "unhealthy"
        
        # Overall health status
        status_value = "healthy" if db_health == "healthy" else "unhealthy"
        
        return {
            "status": status_value,
            "database": db_health,
            "version": "1.0.0"
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )
