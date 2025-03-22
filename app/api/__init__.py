from fastapi import APIRouter

from app.api import exports, health, jobs, titles

# Create API router
api_router = APIRouter()

# Include routers for each endpoint
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["jobs"]
)

api_router.include_router(
    titles.router,
    prefix="/jobs/{job_id}/titles",
    tags=["titles"]
)

api_router.include_router(
    exports.router,
    prefix="/jobs/{job_id}/export",
    tags=["exports"]
)

__all__ = ['api_router']
