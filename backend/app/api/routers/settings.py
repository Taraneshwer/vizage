"""
System settings management endpoints.
"""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/settings", tags=["System"])

@router.get("/")
async def get_settings():
    """
    Retrieves safe system configuration values.
    """
    return {
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    }
