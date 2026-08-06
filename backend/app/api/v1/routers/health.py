from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.dependencies import get_db
from app.core.version import __version__
from loguru import logger

router = APIRouter(prefix="/health", tags=["Health"])

class HealthResponse(BaseModel):
    status: str
    version: str

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

@router.get("/live", response_model=HealthResponse, summary="Liveness Probe")
async def check_live():
    return {"status": "ok", "version": "1.0.0"}

@router.get("/ready", response_model=HealthResponse, summary="Readiness Probe")
async def check_ready():
    return {"status": "ok", "version": "1.0.0"}

