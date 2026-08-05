"""
System health and status endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.dependencies import get_db
from app.core.version import __version__
from loguru import logger

router = APIRouter(prefix="/health", tags=["System"])

@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Returns the system health status, verifying database connectivity.
    """
    db_status = "offline"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "online"
    except Exception as e:
        logger.error(f"Health check failed to connect to DB: {e}")
    
    return {
        "status": "online",
        "version": __version__,
        "database": db_status
    }
