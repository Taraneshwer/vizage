"""
MaskShield AI REST API Entrypoint.
Initializes the Runtime Engine and mounts FastAPI routes.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.services.runtime.startup import initialize_runtime
from app.services.runtime.shutdown import shutdown_runtime
from app.db.session import init_db
from app.services.ai.inference_engine import InferenceEngine
from app.services.runtime.camera_runtime import CameraRuntime
from app.services.orchestrators.recognition_orchestrator import RecognitionOrchestrator
from app.services.orchestrators.enrollment_orchestrator import EnrollmentOrchestrator
from app.services.runtime.inspector import RuntimeInspector
from app.sources.base import StreamingSource
from app.sources.schemas import BaseSourceConfig

from app.api.v1.exceptions.handlers import setup_exception_handlers
from app.api.v1.routers import health, system, camera, runtime, recognition, enrollment, settings, history
from app.api.v1.websockets import routers as ws_routers
from app.api.v1.websockets.manager import StreamingManager
from app.api.v1.websockets.event_bridge import EventBridge
from app.api.v1.websockets.log_sink import WebSocketLogSink
from app.api.v1.websockets.schemas import SystemMessage, RuntimeMessage
from app.core.events import EventBus
import asyncio
import time

# Import source providers at module level to trigger @SourceFactory.register decorators
import app.sources.providers.webcam   # noqa: F401
import app.sources.providers.rtsp     # noqa: F401
import app.sources.providers.ip_camera  # noqa: F401

class MockSource(StreamingSource):
    # Fallback mock source if no specific source is injected
    def __init__(self):
        super().__init__(BaseSourceConfig(source_id="default_camera"))
    def get_capabilities(self): 
        from app.sources.schemas import SourceCapabilities
        return SourceCapabilities()
    async def connect(self): return True
    async def disconnect(self): pass
    async def start(self): pass
    async def stop(self): pass
    async def pause(self): pass
    async def resume(self): pass
    async def read_frame(self): return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up MaskShield AI Backend...")
    
    # 0. Initialize Database
    await init_db()
    
    # 1. Initialize Runtime (GPU, Models)
    model_manager = initialize_runtime()
    
    # 2. Instantiate Engine Services
    from app.services.ai.performance_monitor import PerformanceMonitor
    perf_monitor = PerformanceMonitor()
    inference_engine = InferenceEngine(model_manager=model_manager, perf_monitor=perf_monitor)
    
    # 3. Instantiate Runtimes & Orchestrators
    from app.db.session import AsyncSessionLocal
    from app.db.repository.camera_repo import CameraRepository
    from app.sources.factory import SourceFactory
    from app.sources.schemas import WebcamConfig, RTSPConfig
    
    default_source = MockSource()
    camera_id = "default_camera"
    
    try:
        async with AsyncSessionLocal() as session:
            repo = CameraRepository(session)
            active_cam = await repo.get_active()
            if active_cam:
                camera_id = active_cam.id
                if active_cam.source_type == "WEBCAM":
                    config = WebcamConfig(source_id=active_cam.id, camera_index=int(active_cam.connection_url))
                    default_source = SourceFactory.create("webcam", config)
                elif active_cam.source_type == "RTSP":
                    config = RTSPConfig(source_id=active_cam.id, rtsp_url=active_cam.connection_url)
                    default_source = SourceFactory.create("rtsp", config)
    except Exception as e:
        logger.error(f"Failed to load active camera from DB, falling back to mock: {e}")
        
    camera_runtime = CameraRuntime(camera_id=camera_id, source=default_source)
    
    recognition_orchestrator = RecognitionOrchestrator(
        camera_runtime=camera_runtime,
        inference_engine=inference_engine
    )
    
    # We need FAISSService for enrollment
    try:
        faiss_service = model_manager.get_service("FAISS")
    except KeyError:
        # Mock for missing FAISS in this specific startup if not registered
        faiss_service = None
        
    enrollment_orchestrator = EnrollmentOrchestrator(
        inference_engine=inference_engine,
        faiss_service=faiss_service
    )
    
    runtime_inspector = RuntimeInspector(model_manager=model_manager)
    
    # 4. Initialize WebSockets & Streaming
    streaming_manager = StreamingManager()
    event_bus = EventBus()
    event_bridge = EventBridge(event_bus, streaming_manager)
    
    # Wire the camera frame broadcaster into the recognition orchestrator
    # so every frame received is broadcast to WS /ws/camera clients.
    # CameraRuntime calls callbacks synchronously, so we schedule async work via create_task.
    _orig_frame_callback = recognition_orchestrator._on_frame_received
    def _combined_frame_callback(frame):
        """Calls the orchestrator pipeline AND schedules a camera frame broadcast."""
        # Schedule the async broadcast (non-blocking)
        asyncio.get_event_loop().create_task(event_bridge.broadcast_camera_frame(
            camera_id=camera_runtime.camera_id,
            frame_id=frame.frame_id,
            image_matrix=frame.image
        ))
        # Run the synchronous orchestrator callback
        _orig_frame_callback(frame)
    
    camera_runtime.set_callback(_combined_frame_callback)
    
    # Log sink
    loop = asyncio.get_running_loop()
    log_sink = WebSocketLogSink(loop)
    logger.add(log_sink.write, format="{message}")
    
    # Attach to App State for Dependency Injection
    app.state.model_manager = model_manager
    app.state.inference_engine = inference_engine
    app.state.camera_runtime = camera_runtime
    app.state.recognition_orchestrator = recognition_orchestrator
    app.state.enrollment_orchestrator = enrollment_orchestrator
    app.state.runtime_inspector = runtime_inspector
    app.state.streaming_manager = streaming_manager
    
    # Background Ticker for Metrics
    async def metrics_ticker():
        while True:
            await asyncio.sleep(1.0)
            
            # Runtime stats
            r_stats = recognition_orchestrator.session_manager.get_session_stats()
            r_msg = RuntimeMessage(
                topic="runtime",
                timestamp=time.time(),
                state=r_stats.get("state", "STOPPED"),
                total_frames_processed=r_stats.get("total_frames_processed", 0),
                average_fps=r_stats.get("average_fps", 0.0),
                total_recognitions=r_stats.get("total_recognitions", 0),
                total_unknowns=r_stats.get("total_unknowns", 0),
                dropped_frames=r_stats.get("dropped_frames", 0)
            )
            await streaming_manager.broadcast("runtime", r_msg.model_dump_json())
            
            # System stats (can be slower, e.g., every 5s, but 1s is fine for streaming UI)
            sys_report = runtime_inspector.generate_report()
            s_msg = SystemMessage(
                topic="system",
                timestamp=time.time(),
                gpu=sys_report["gpu"],
                models=sys_report["models"],
                health=sys_report["health"]
            )
            await streaming_manager.broadcast("system", s_msg.model_dump_json())
            
    ticker_task = loop.create_task(metrics_ticker())
    
    yield
    
    # Shutdown
    logger.info("Shutting down MaskShield AI Backend...")
    ticker_task.cancel()
    await recognition_orchestrator.stop_session()
    shutdown_runtime(model_manager)

app = FastAPI(
    title="MaskShield AI REST API",
    description="Backend API for MaskShield AI Hybrid Multi-Cue Recognition System.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
setup_exception_handlers(app)

# Include Routers
api_v1_prefix = "/api/v1"
app.include_router(health.router)
app.include_router(system.router, prefix=api_v1_prefix)
app.include_router(camera.router, prefix=api_v1_prefix)
app.include_router(runtime.router, prefix=api_v1_prefix)
app.include_router(recognition.router, prefix=api_v1_prefix)
app.include_router(enrollment.router, prefix=api_v1_prefix)
app.include_router(settings.router, prefix=api_v1_prefix)
app.include_router(history.router, prefix=api_v1_prefix)

# Include WebSocket Routers
app.include_router(ws_routers.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
