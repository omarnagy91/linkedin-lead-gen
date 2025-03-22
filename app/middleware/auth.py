import logging
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.models.api import ErrorResponse
from app.utils.config import settings
from app.utils.errors import UnauthorizedError

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process the request and check for valid API key.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response from the next handler or an error response
        """
        # Skip authentication for health check
        if request.url.path == "/api/health":
            return await call_next(request)
        
        # Check for API key in headers
        api_key = request.headers.get("Authorization")
        
        if not api_key:
            logger.warning("Missing API key in request")
            return JSONResponse(
                status_code=401,
                content=ErrorResponse(
                    error=True,
                    message="Missing API key",
                    code="UNAUTHORIZED"
                ).dict()
            )
        
        # Check if API key is valid
        if not api_key.startswith("Bearer "):
            logger.warning("Invalid API key format")
            return JSONResponse(
                status_code=401,
                content=ErrorResponse(
                    error=True,
                    message="Invalid API key format",
                    code="UNAUTHORIZED"
                ).dict()
            )
        
        # Extract the key
        key = api_key.split("Bearer ")[1].strip()
        
        if key != settings.API_KEY:
            logger.warning("Invalid API key")
            return JSONResponse(
                status_code=401,
                content=ErrorResponse(
                    error=True,
                    message="Invalid API key",
                    code="UNAUTHORIZED"
                ).dict()
            )
        
        # API key is valid, continue
        return await call_next(request)
