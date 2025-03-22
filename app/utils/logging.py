import logging
import sys
from typing import Any, Dict, Optional

from app.utils.config import settings


def setup_logging() -> None:
    """
    Configure logging for the application.
    """
    # Set up root logger
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set levels for third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Create application logger
    logger = logging.getLogger("app")
    logger.setLevel(log_level)
    
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context information to log messages.
    """
    
    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        """
        Initialize the logger adapter.
        
        Args:
            logger: The logger to adapt
            extra: Extra context information
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        """
        Process the log message.
        
        Args:
            msg: The log message
            kwargs: Additional keyword arguments
            
        Returns:
            Tuple: The processed message and kwargs
        """
        job_id = self.extra.get("job_id")
        
        if job_id:
            msg = f"[Job {job_id}] {msg}"
        
        return msg, kwargs


def get_logger(name: str, job_id: Optional[str] = None) -> LoggerAdapter:
    """
    Get a logger with optional job context.
    
    Args:
        name: The logger name
        job_id: Optional job ID for context
        
    Returns:
        LoggerAdapter: The configured logger
    """
    logger = logging.getLogger(name)
    
    if job_id:
        return LoggerAdapter(logger, {"job_id": job_id})
    
    return LoggerAdapter(logger, {})
