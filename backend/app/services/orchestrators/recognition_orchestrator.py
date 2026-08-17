"""
Recognition Orchestrator.
The definitive entrypoint for live inference. Coordinates Camera, InferenceEngine, and Event Bus.
"""
import asyncio
from typing import Optional
from app.core.logger import get_logger
from app.core.events import EventBus, RecognitionEvent, UnknownDetectedEvent, ErrorEvent, HistoryEvent
from app.services.runtime.camera_runtime import CameraRuntime
from app.services.runtime.session_manager import RuntimeSessionManager
from app.services.runtime.pipeline import RuntimePipeline, LoggingMiddleware, MemoryOptimizationMiddleware
from app.services.runtime.recovery import ErrorRecoveryManager
from app.services.ai.inference_engine import InferenceEngine
from app.sources.frame import Frame
from app.services.ai.models import RecognitionState
from app.db.session import AsyncSessionLocal
from app.db.models import RecognitionHistory, Identity
from app.db.repository.camera_repo import CameraRepository
from app.sources.factory import SourceFactory
from app.sources.schemas import WebcamConfig, RTSPConfig
from sqlalchemy import select
from datetime import datetime

logger = get_logger(__name__)

class RecognitionOrchestrator:
    def __init__(self, camera_runtime: CameraRuntime, inference_engine: InferenceEngine):
        self.camera_runtime = camera_runtime
        self.inference_engine = inference_engine
        
        self.event_bus = EventBus()
        self.session_manager = RuntimeSessionManager(camera_runtime.camera_id)
        self.recovery_manager = ErrorRecoveryManager()
        self._camera_task: asyncio.Task = None
        
        self.pipeline = RuntimePipeline()
        self.pipeline.add_middleware(LoggingMiddleware())
        self.pipeline.add_middleware(MemoryOptimizationMiddleware())
        
        self._last_logged_tracks: dict[str, float] = {}
        
        self.camera_runtime.set_callback(self._on_frame_received)
        
    async def start_session(self, active_cam: Optional[object] = None) -> None:
        if self._camera_task and not self._camera_task.done():
            logger.warning("Session already running.")
            return
            
        if active_cam:
            try:
                logger.info(f"Loading active camera configuration: {active_cam.name} ({active_cam.source_type})")
                if active_cam.source_type == "WEBCAM":
                    config = WebcamConfig(source_id=active_cam.id, camera_index=int(active_cam.connection_url))
                    source = SourceFactory.create("webcam", config)
                elif active_cam.source_type == "RTSP":
                    config = RTSPConfig(source_id=active_cam.id, rtsp_url=active_cam.connection_url)
                    source = SourceFactory.create("rtsp", config)
                else:
                    logger.warning(f"Unknown source type: {active_cam.source_type}, using current source.")
                    source = None
                    
                if source:
                    self.camera_runtime.camera_id = active_cam.id
                    self.camera_runtime.source = source
                    self.session_manager.camera_id = active_cam.id
            except Exception as e:
                logger.error(f"Failed to load active camera configuration: {e}")
            
        self.session_manager.set_state("RUNNING")
        self._camera_task = asyncio.create_task(self.camera_runtime.start())
        logger.info("Camera runtime task started in background.")
        
    async def stop_session(self) -> None:
        self.session_manager.set_state("STOPPED")
        await self.camera_runtime.stop()
        if self._camera_task and not self._camera_task.done():
            self._camera_task.cancel()
            try:
                await self._camera_task
            except asyncio.CancelledError:
                pass
            self._camera_task = None
        logger.info("Camera runtime task stopped.")

    async def switch_active_camera(self, active_cam: object) -> None:
        """Performs a hot switch of the active camera config, restarting the stream."""
        logger.info(f"Switching active camera to: {active_cam.id if active_cam else 'None'}")
        was_running = self._camera_task and not self._camera_task.done()
        
        if was_running:
            logger.info("Stopping running camera session for hot switch...")
            await self.stop_session()
            
        logger.info("Activating camera session with the new active camera...")
        await self.start_session(active_cam)

    def _on_frame_received(self, frame: Frame) -> None:
        """Called by CameraRuntime when a frame is ready. Non-blocking dispatcher."""
        if self._is_inferencing:
            # Skip queueing intermediate frames to maintain 0ms latency and 0 thread pool backlog
            return
        self._is_inferencing = True
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._on_frame_received_async(frame))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.create_task(self._on_frame_received_async(frame))
        except Exception as e:
            self._is_inferencing = False
            logger.error(f"Error dispatching frame: {e}")

    async def _on_frame_received_async(self, frame: Frame) -> None:
        """Asynchronous pipeline execution using thread pool for ML inference."""
        try:
            import time
            t_dequeue = time.time()
            t_preprocess_start = time.time()
            
            frame = self.pipeline.run_before(frame)
            t_preprocess_end = time.time()
            
            t_inference_start = time.time()
            context = await asyncio.to_thread(self.inference_engine.process_frame, frame)
            t_inference_end = time.time()
            
            t_postprocess_start = time.time()
            context = self.pipeline.run_after(context)
            t_postprocess_end = time.time()
            
            latency_queue = (t_dequeue - frame.timestamp) * 1000
            latency_preprocess = (t_preprocess_end - t_preprocess_start) * 1000
            latency_inference = (t_inference_end - t_inference_start) * 1000
            latency_postprocess = (t_postprocess_end - t_postprocess_start) * 1000
            latency_total = (t_postprocess_end - frame.timestamp) * 1000
            
            logger.debug(
                f"[Latency Tracker] Frame={frame.frame_id} | "
                f"Queue={latency_queue:.1f}ms | "
                f"Pre={latency_preprocess:.1f}ms | "
                f"Inf={latency_inference:.1f}ms | "
                f"Post={latency_postprocess:.1f}ms | "
                f"Backend E2E={latency_total:.1f}ms"
            )
            
            now_sec = time.time()
            for res in context.detections:
                self.session_manager.log_recognition(res.is_unknown, res.verification_score)
                
                # Debounce database history saves per track to eliminate DB write locks
                track_id = res.tracking_id or "untracked"
                identity_key = res.candidate.identity_id if (not res.is_unknown and res.candidate) else "unknown"
                track_key = f"{track_id}_{identity_key}"
                
                last_logged = self._last_logged_tracks.get(track_key, 0.0)
                if (now_sec - last_logged) >= 5.0:
                    self._last_logged_tracks[track_key] = now_sec
                    asyncio.create_task(self._save_history_event(frame, res, context))
                
                if res.is_unknown:
                    # Publish Unknown event for internal triggers
                    self.event_bus.publish_sync(UnknownDetectedEvent(
                        camera_id=self.camera_runtime.camera_id,
                        frame_id=frame.frame_id,
                        tracking_id=res.tracking_id or "untracked"
                    ))
                
                # ALWAYS publish Recognition event for frontend websockets (to draw bounding boxes)
                identity_id = res.candidate.identity_id if (res.state == RecognitionState.RECOGNIZED and res.candidate) else "Unknown"
                score = res.verification_score if (res.state == RecognitionState.RECOGNIZED and res.candidate) else res.detection.confidence
                
                self.event_bus.publish_sync(RecognitionEvent(
                    identity_id=identity_id,
                    verification_score=score,
                    bbox=(res.detection.bbox.x1, res.detection.bbox.y1, res.detection.bbox.x2, res.detection.bbox.y2),
                    camera_id=self.camera_runtime.camera_id,
                    frame_id=frame.frame_id,
                    tracking_id=res.tracking_id or "untracked",
                    mask_status=res.mask.has_mask if res.mask else False,
                    recognition_mode="Upper" if (res.embedding and getattr(res.embedding, 'is_upper_face', False)) else "Full",
                    processing_time_ms=context.timers.get("yolo_detection_duration", 0) + context.timers.get("adaface_embedding_duration", 0),
                    capture_timestamp=frame.timestamp
                ))
                    
            total_time = sum([v for k, v in context.timers.items() if k.endswith("_duration")])
            self.session_manager.log_frame(fps=0.0, processing_time_ms=total_time)
            
        except Exception as e:
            self.session_manager.log_error()
            self.recovery_manager.handle_exception(e, source=f"RecognitionOrchestrator-{self.camera_runtime.camera_id}")
            self.event_bus.publish_sync(ErrorEvent(
                source="RecognitionOrchestrator",
                error_msg=str(e)
            ))
        finally:
            self._is_inferencing = False

    async def _save_history_event(self, frame, res, context):
        try:
            async with AsyncSessionLocal() as session:
                name = None
                department = None
                
                                                             
                if not res.is_unknown and res.candidate:
                    stmt = select(Identity).where(Identity.identity_id == res.candidate.identity_id)
                    db_res = await session.execute(stmt)
                    ident = db_res.scalar_one_or_none()
                    if ident:
                        name = ident.name
                        department = ident.department
                        ident.recognition_count += 1
                        ident.last_seen = datetime.utcnow()
                        
                history = RecognitionHistory(
                    timestamp=datetime.utcnow(),
                    identity_id=res.candidate.identity_id if not res.is_unknown and res.candidate else None,
                    name=name,
                    department=department,
                    verification_score=int(res.verification_score * 100),
                    mode="Unknown" if res.is_unknown else ("Upper" if (res.embedding and getattr(res.embedding, 'is_upper_face', False)) else "Full"),
                    camera_id=self.camera_runtime.camera_id,
                    tracking_id=res.tracking_id or "untracked",
                    processing_time_ms=context.timers.get("yolo_detection_duration", 0) + context.timers.get("adaface_embedding_duration", 0),
                    state="UNKNOWN" if res.is_unknown else res.state.value,
                    has_mask=res.mask.has_mask if res.mask else False
                )
                session.add(history)
                await session.commit()
                
                                       
                self.event_bus.publish_sync(HistoryEvent(
                    history_id=history.id,
                    timestamp=history.timestamp.isoformat(),
                    identity_id=history.identity_id,
                    name=history.name,
                    department=history.department,
                    verification_score=history.verification_score,
                    mode=history.mode,
                    camera_id=history.camera_id,
                    tracking_id=history.tracking_id,
                    processing_time_ms=history.processing_time_ms,
                    state=history.state,
                    has_mask=history.has_mask
                ))
                
        except Exception as e:
            logger.error(f"Failed to save history event: {e}")
