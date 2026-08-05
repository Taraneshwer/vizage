"""
Runtime Session Manager.
Tracks global runtime statistics for a specific camera orchestrator session.
"""
import time
import uuid
from typing import Optional
from pydantic import BaseModel
from app.core.logger import get_logger
from app.services.ai.gpu_manager import GPUManager

logger = get_logger(__name__)

class RuntimeSessionState(BaseModel):
    session_id: str
    camera_id: str
    state: str # INIT, RUNNING, RECOVERING, STOPPED
    runtime_seconds: float
    current_fps: float
    frames_processed: int
    dropped_frames: int
    recognitions_count: int
    unknowns_count: int
    error_count: int
    gpu_memory_mb: int

class RuntimeSessionManager:
    def __init__(self, camera_id: str):
        self.session_id = str(uuid.uuid4())
        self.camera_id = camera_id
        self.start_time = time.time()
        self.state = "INIT"
        
        self.frames_processed = 0
        self.dropped_frames = 0
        self.recognitions_count = 0
        self.unknowns_count = 0
        self.error_count = 0
        
        self._frame_times = []
        self._last_time = time.time()
        self.gpu_manager = GPUManager()
        
    def set_state(self, state: str):
        self.state = state
        
    def log_frame(self):
        self.frames_processed += 1
        now = time.time()
        self._frame_times.append(now - self._last_time)
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)
        self._last_time = now
        
    def log_drop(self):
        self.dropped_frames += 1
        
    def log_error(self):
        self.error_count += 1
        
    def log_recognition(self, is_unknown: bool):
        if is_unknown:
            self.unknowns_count += 1
        else:
            self.recognitions_count += 1
            
    def get_fps(self) -> float:
        if not self._frame_times:
            return 0.0
        avg = sum(self._frame_times) / len(self._frame_times)
        return 1.0 / avg if avg > 0 else 0.0
        
    def get_state(self) -> RuntimeSessionState:
        gpu_stat = self.gpu_manager.get_status()
        return RuntimeSessionState(
            session_id=self.session_id,
            camera_id=self.camera_id,
            state=self.state,
            runtime_seconds=time.time() - self.start_time,
            current_fps=self.get_fps(),
            frames_processed=self.frames_processed,
            dropped_frames=self.dropped_frames,
            recognitions_count=self.recognitions_count,
            unknowns_count=self.unknowns_count,
            error_count=self.error_count,
            gpu_memory_mb=gpu_stat.allocated_memory_mb if gpu_stat.is_available else 0
        )
