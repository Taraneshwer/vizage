"""
Enrollment Orchestrator.
Manages transactional enrollment workflows without API routing logic.
"""
from typing import List, Optional
from pydantic import BaseModel
from app.core.logger import get_logger
from app.sources.frame import Frame
from app.services.ai.inference_engine import InferenceEngine
from app.services.ai.faiss_service import FAISSService
from app.core.events import EventBus, AppEvent

logger = get_logger(__name__)

class EnrollmentResult(BaseModel):
    success: bool
    identity_id: Optional[str] = None
    error_msg: Optional[str] = None

class EnrollmentStartedEvent(AppEvent):
    identity_id: str

class EnrollmentCompletedEvent(AppEvent):
    identity_id: str
    success: bool
    
class EnrollmentOrchestrator:
    def __init__(self, inference_engine: InferenceEngine, faiss_service: FAISSService):
        self.inference = inference_engine
        self.faiss = faiss_service
        self.event_bus = EventBus()
        
    def enroll_person(self, identity_id: str, name: str, frames: List[Frame]) -> EnrollmentResult:
        """
        Processes a list of frames, checks quality, generates embeddings, and inserts them.
        Transactional: if one fails, we don't save.
        """
        self.event_bus.publish_sync(EnrollmentStartedEvent(identity_id=identity_id))
        
        valid_embeddings = []
        for frame in frames:
            context = self.inference.process_frame(frame)
            
            # We assume for enrollment, there should be exactly ONE face per frame
            if len(context.detections) != 1:
                return self._fail(identity_id, f"Frame must contain exactly 1 face. Found {len(context.detections)}.")
                
            det = context.detections[0]
            
            if det.detection.confidence < 0.70:
                return self._fail(identity_id, "Face detection quality too low for enrollment.")
                
            # Disallow masks during enrollment for best quality
            if det.mask and det.mask.has_mask:
                return self._fail(identity_id, "Cannot enroll while wearing a mask.")
                
            if not det.embedding:
                return self._fail(identity_id, "Failed to generate embedding.")
                
            valid_embeddings.append(det.embedding)
            
        if not valid_embeddings:
            return self._fail(identity_id, "No valid frames provided.")
            
        # Insert into FAISS
        try:
            # Here we just insert the best/first one for simplicity, or we could aggregate
            self.faiss.add_embedding(identity_id=identity_id, embedding=valid_embeddings[0])
            self.faiss.save_index() # Persist
        except Exception as e:
            logger.error(f"Failed to save FAISS during enrollment: {e}")
            return self._fail(identity_id, f"Database insertion failed: {e}")
            
        # Future: Persist to SQLite using SQLAlchemy repository here
        
        self.event_bus.publish_sync(EnrollmentCompletedEvent(identity_id=identity_id, success=True))
        return EnrollmentResult(success=True, identity_id=identity_id)
        
    def _fail(self, identity_id: str, msg: str) -> EnrollmentResult:
        logger.warning(f"Enrollment failed for {identity_id}: {msg}")
        self.event_bus.publish_sync(EnrollmentCompletedEvent(identity_id=identity_id, success=False))
        return EnrollmentResult(success=False, error_msg=msg)
