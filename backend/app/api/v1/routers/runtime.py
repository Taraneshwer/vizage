from fastapi import APIRouter, Depends
from app.api.v1.schemas.api_schemas import RuntimeStatsResponse
from app.api.v1.dependencies import get_recognition_orchestrator
from app.services.orchestrators.recognition_orchestrator import RecognitionOrchestrator

router = APIRouter(prefix="/runtime", tags=["Runtime"])

@router.get("/stats", response_model=RuntimeStatsResponse, summary="Get Runtime Stats")
async def get_runtime_stats(orchestrator: RecognitionOrchestrator = Depends(get_recognition_orchestrator)):
    manager = orchestrator.session_manager
    state = manager.get_state()
    return RuntimeStatsResponse(
        state=state.state,
        total_frames_processed=state.frames_processed,
        total_recognitions=state.recognitions_count,
        total_unknowns=state.unknowns_count,
        errors=state.error_count,
        uptime_seconds=state.runtime_seconds,
        average_fps=state.current_fps
    )

from app.api.v1.schemas.api_schemas import BaseResponse

@router.post("/start", response_model=BaseResponse, summary="Start Runtime Engine")
async def start_runtime(orchestrator: RecognitionOrchestrator = Depends(get_recognition_orchestrator)):
    await orchestrator.start_session()
    return BaseResponse(success=True, message="Runtime Engine started successfully.")

@router.post("/stop", response_model=BaseResponse, summary="Stop Runtime Engine")
async def stop_runtime(orchestrator: RecognitionOrchestrator = Depends(get_recognition_orchestrator)):
    await orchestrator.stop_session()
    return BaseResponse(success=True, message="Runtime Engine stopped successfully.")
