from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.db.models import CameraSource
from app.db.repository.camera_repo import CameraRepository
from app.api.v1.schemas.api_schemas import (
    CameraConnectionRequest, 
    CameraStatusResponse, 
    BaseResponse,
    CameraSourceModel,
    CameraSourceCreateRequest,
    CameraSourceUpdateRequest
)
from app.api.v1.dependencies import get_camera_runtime, get_recognition_orchestrator
from app.services.runtime.camera_runtime import CameraRuntime
from app.services.orchestrators.recognition_orchestrator import RecognitionOrchestrator
from app.api.v1.exceptions.handlers import CameraException

router = APIRouter(prefix="/camera", tags=["Camera"])

@router.get("", response_model=List[CameraSourceModel], summary="List Configured Cameras")
async def list_cameras(session: AsyncSession = Depends(get_db_session)):
    repo = CameraRepository(session)
    cameras = await repo.get_all()
    return [
        CameraSourceModel(
            id=c.id,
            name=c.name,
            source_type=c.source_type,
            connection_url=c.connection_url,
            is_active=c.is_active,
            created_at=c.created_at.isoformat()
        ) for c in cameras
    ]

@router.post("", response_model=CameraSourceModel, summary="Add New Camera")
async def add_camera(data: CameraSourceCreateRequest, session: AsyncSession = Depends(get_db_session)):
    repo = CameraRepository(session)
    camera = CameraSource(
        name=data.name,
        source_type=data.source_type,
        connection_url=data.connection_url
    )
    repo.add(camera)
    await session.flush()
    await session.refresh(camera)
    
    return CameraSourceModel(
        id=camera.id,
        name=camera.name,
        source_type=camera.source_type,
        connection_url=camera.connection_url,
        is_active=camera.is_active,
        created_at=camera.created_at.isoformat()
    )

# IMPORTANT: Literal path segments must come BEFORE path parameter routes.
# These routes (/available, /start, /stop, /status) must be declared before /{camera_id}
# to prevent FastAPI from matching them as camera_id parameters.

@router.get("/available", response_model=Dict[str, Any], summary="List Available Sources")
async def get_available_sources():
    """Returns a list of connected webcams or source capabilities."""
    try:
        from app.sources.discovery import SourceDiscovery
        sources = SourceDiscovery.list_available_cameras()
        return {"success": True, "sources": sources}
    except Exception as e:
        return {"success": False, "sources": [], "message": str(e)}

@router.post("/start", response_model=BaseResponse, summary="Start Camera Stream")
async def start_camera(orchestrator: RecognitionOrchestrator = Depends(get_recognition_orchestrator)):
    """Starts the orchestrator and camera loop."""
    try:
        await orchestrator.start_session()
        return BaseResponse(success=True, message="Camera started.")
    except Exception as e:
        raise CameraException(f"Failed to start camera: {e}")

@router.post("/stop", response_model=BaseResponse, summary="Stop Camera Stream")
async def stop_camera(orchestrator: RecognitionOrchestrator = Depends(get_recognition_orchestrator)):
    """Stops the orchestrator and camera loop."""
    try:
        await orchestrator.stop_session()
        return BaseResponse(success=True, message="Camera stopped.")
    except Exception as e:
        raise CameraException(f"Failed to stop camera: {e}")

@router.get("/status", response_model=CameraStatusResponse, summary="Get Camera Status")
async def get_camera_status(runtime: CameraRuntime = Depends(get_camera_runtime)):
    if not runtime.session:
        return CameraStatusResponse(
            success=True,
            camera_id=runtime.camera_id,
            is_active=False,
            uptime=0.0,
            fps=0.0,
            dropped_frames=0
        )
    
    stats = runtime.session.get_session_stats()
    return CameraStatusResponse(
        success=True,
        camera_id=runtime.camera_id,
        is_active=runtime.is_running,
        uptime=stats.get("uptime_seconds", 0.0),
        fps=stats.get("average_fps", 0.0),
        dropped_frames=stats.get("dropped_frames", 0)
    )

@router.put("/{camera_id}", response_model=BaseResponse, summary="Update Camera")
async def update_camera(camera_id: str, data: CameraSourceUpdateRequest, session: AsyncSession = Depends(get_db_session)):
    repo = CameraRepository(session)
    camera = await repo.get(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    if data.name is not None:
        camera.name = data.name
    if data.source_type is not None:
        camera.source_type = data.source_type
    if data.connection_url is not None:
        camera.connection_url = data.connection_url
    
    return BaseResponse(success=True, message="Camera updated successfully")

@router.post("/{camera_id}/activate", response_model=BaseResponse, summary="Set Active Camera")
async def activate_camera(camera_id: str, session: AsyncSession = Depends(get_db_session)):
    repo = CameraRepository(session)
    camera = await repo.get(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    await repo.set_active(camera_id)
    return BaseResponse(success=True, message=f"Camera {camera.name} set as active")

@router.delete("/{camera_id}", response_model=BaseResponse, summary="Delete Camera")
async def delete_camera(camera_id: str, session: AsyncSession = Depends(get_db_session)):
    repo = CameraRepository(session)
    camera = await repo.get(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    await repo.delete(camera)
    return BaseResponse(success=True, message="Camera deleted successfully")
