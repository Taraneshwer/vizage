from fastapi import APIRouter, Depends
from app.api.v1.schemas.api_schemas import SystemHealthResponse
from app.api.v1.dependencies import get_runtime_inspector
from app.services.runtime.inspector import RuntimeInspector

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/info", response_model=SystemHealthResponse, summary="Get Runtime Diagnostics")
async def get_system_info(inspector: RuntimeInspector = Depends(get_runtime_inspector)):
    """Retrieves full point-in-time diagnostics of GPU, Models, and System."""
    report = inspector.generate_report()
    return SystemHealthResponse(**report)
