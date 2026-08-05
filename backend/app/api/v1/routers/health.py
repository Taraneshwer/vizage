from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["Health"])

class HealthResponse(BaseModel):
    status: str
    version: str

@router.get("/live", response_model=HealthResponse, summary="Liveness Probe")
async def check_live():
    return {"status": "ok", "version": "1.0.0"}

@router.get("/ready", response_model=HealthResponse, summary="Readiness Probe")
async def check_ready():
    return {"status": "ok", "version": "1.0.0"}
