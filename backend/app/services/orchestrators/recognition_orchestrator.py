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
        
        # Bind the callback
        self.camera_runtime.set_callback(self._on_frame_received)
        
    async def start_session(self) -> None:
        if self._camera_task and not self._camera_task.done():
            logger.warning("Session already running.")
            return
        self.session_manager.set_state("RUNNING")
        # Run the infinite camera loop as a background task so the event loop stays free
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
        
    def _on_frame_received(self, frame: Frame) -> None:
        """Called by CameraRuntime when a frame is ready."""
        try:
            # 1. Pipeline Before
            frame = self.pipeline.run_before(frame)
            
            # 2. Inference Engine (Detection -> Alignment -> AdaFace -> FAISS -> Decision)
            context = self.inference_engine.process_frame(frame)
            
            # 3. Pipeline After
            context = self.pipeline.run_after(context)
            
            # 4. Handle Results and Events
            for res in context.detections:
                # Update Session Stats
                self.session_manager.log_recognition(res.is_unknown, res.verification_score)
                
                # Asynchronously save to SQLite
                loop = asyncio.get_event_loop()
                loop.create_task(self._save_history_event(frame, res, context))
                
                if res.is_unknown:
                    # Fire Unknown Event
                    self.event_bus.publish_sync(UnknownDetectedEvent(
                        camera_id=self.camera_runtime.camera_id,
                        frame_id=frame.frame_id,
                        tracking_id=res.tracking_id or "untracked"
                    ))
                elif res.state == RecognitionState.RECOGNIZED and res.candidate:
                    # Fire Recognition Event
                    self.event_bus.publish_sync(RecognitionEvent(
                        identity_id=res.candidate.identity_id,
                        verification_score=res.verification_score,
                        bbox=(res.detection.bbox.x1, res.detection.bbox.y1, res.detection.bbox.x2, res.detection.bbox.y2),
                        camera_id=self.camera_runtime.camera_id,
                        frame_id=frame.frame_id,
                        tracking_id=res.tracking_id or "untracked",
                        mask_status=res.mask.has_mask if res.mask else False,
                        recognition_mode="Upper" if (res.embedding and getattr(res.embedding, 'is_upper_face', False)) else "Full",
                        processing_time_ms=context.timers.get("yolo_detection_duration", 0) + context.timers.get("adaface_embedding_duration", 0)
                    ))
                    
            # 5. Log Session Frame
            total_time = sum([v for k, v in context.timers.items() if k.endswith("_duration")])
            self.session_manager.log_frame(fps=0.0, processing_time_ms=total_time) # fps will be tracked dynamically
            
        except Exception as e:
            self.session_manager.log_error()
            self.recovery_manager.handle_exception(e, source=f"RecognitionOrchestrator-{self.camera_runtime.camera_id}")
            self.event_bus.publish_sync(ErrorEvent(
                source="RecognitionOrchestrator",
                error_msg=str(e)
            ))

    async def _save_history_event(self, frame, res, context):
        try:
            async with AsyncSessionLocal() as session:
                name = None
                department = None
                
                # If known, fetch details to cache in history
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
                
                # Publish history event
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
