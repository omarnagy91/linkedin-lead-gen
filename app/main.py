import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.api import api_router
from app.middleware.auth import AuthMiddleware
from app.utils.config import settings
from app.utils.errors import error_handler
from app.utils.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LinkedIn Lead Generation API",
    description="API for LinkedIn lead generation using GPT-4, SerpAPI, and ProxyCurl",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
    openapi_url=None,  # Disable default openapi.json
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Add exception handlers
app.add_exception_handler(Exception, error_handler)

# Add API router
app.include_router(api_router, prefix=settings.API_PREFIX)


# Custom OpenAPI and documentation endpoints
@app.get("/api/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(
        title="LinkedIn Lead Generation API",
        version="1.0.0",
        description="API for LinkedIn lead generation using GPT-4, SerpAPI, and ProxyCurl",
        routes=app.routes,
    )


@app.get("/api/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="LinkedIn Lead Generation API",
    )


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    """
    logger.info("Starting up LinkedIn Lead Generation API")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    """
    logger.info("Shutting down LinkedIn Lead Generation API")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
