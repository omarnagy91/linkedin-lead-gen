import logging
from typing import Dict, Optional, Union

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.models.api import ErrorResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base exception class for application errors"""
    
    def __init__(
        self, 
        message: str, 
        code: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ValidationError(AppError):
    """Exception for validation errors"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class NotFoundError(AppError):
    """Exception for resource not found errors"""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class UnauthorizedError(AppError):
    """Exception for authentication errors"""
    
    def __init__(self, message: str = "Invalid or missing API key", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class ServiceError(AppError):
    """Exception for external service errors"""
    
    def __init__(self, message: str, service: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=f"{service.upper()}_SERVICE_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for FastAPI.
    
    Args:
        request: The request that caused the exception
        exc: The exception that was raised
        
    Returns:
        JSONResponse: Error response with appropriate status code
    """
    # Handle our custom exceptions
    if isinstance(exc, AppError):
        logger.error(f"AppError: {exc.message}", exc_info=True)
        
        response = ErrorResponse(
            error=True,
            message=exc.message,
            code=exc.code
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response.dict()
        )
    
    # Handle FastAPI's HTTPException
    if isinstance(exc, HTTPException):
        logger.error(f"HTTPException: {exc.detail}", exc_info=True)
        
        response = ErrorResponse(
            error=True,
            message=str(exc.detail),
            code="HTTP_ERROR"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response.dict()
        )
    
    # Handle other exceptions
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    response = ErrorResponse(
        error=True,
        message="An unexpected error occurred",
        code="INTERNAL_SERVER_ERROR"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.dict()
    )
