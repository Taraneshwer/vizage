"""
Recognition Session Manager.
Tracks runtime statistics for the entire session.
"""
import time
from app.core.logger import get_logger
from app.services.ai.models import RecognitionSessionStats

logger = get_logger(__name__)

class RecognitionSessionManager:
    def __init__(self):
        self.start_time = time.time()
        self.frames_processed = 0
        self.recognitions_count = 0
        self.unknowns_count = 0
        self.total_confidence = 0.0
        self.total_processing_time_ms = 0.0
        self.fps = 0.0
        
    def log_frame(self, fps: float, processing_time_ms: float) -> None:
        self.frames_processed += 1
        self.fps = fps
        self.total_processing_time_ms += processing_time_ms
        
    def log_recognition(self, is_unknown: bool, confidence: float) -> None:
        if is_unknown:
            self.unknowns_count += 1
        else:
            self.recognitions_count += 1
            
        self.total_confidence += confidence
        
    def get_stats(self) -> RecognitionSessionStats:
        total_faces = self.recognitions_count + self.unknowns_count
        avg_conf = self.total_confidence / total_faces if total_faces > 0 else 0.0
        avg_time = self.total_processing_time_ms / self.frames_processed if self.frames_processed > 0 else 0.0
        
        return RecognitionSessionStats(
            runtime_seconds=time.time() - self.start_time,
            frames_processed=self.frames_processed,
            recognitions_count=self.recognitions_count,
            unknowns_count=self.unknowns_count,
            average_confidence=avg_conf,
            average_processing_time_ms=avg_time,
            current_fps=self.fps
        )
