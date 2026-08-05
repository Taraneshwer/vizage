"""
WebSocket Stream Message Schemas.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class WSMessageBase(BaseModel):
    topic: str
    timestamp: float

class RecognitionStreamMessage(WSMessageBase):
    identity_id: str
    verification_score: float
    bbox: List[int]
    tracking_id: str
    mask_status: bool
    recognition_mode: str
    processing_time_ms: float

class CameraFrameMessage(WSMessageBase):
    frame_id: int
    camera_id: str
    image_base64: str

class HistoryStreamMessage(WSMessageBase):
    history_id: str
    event_timestamp: str
    identity_id: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None
    verification_score: int
    mode: str
    camera_id: str
    tracking_id: str
    processing_time_ms: int
    state: str
    has_mask: bool

class SystemMessage(WSMessageBase):
    gpu: Dict[str, Any]
    models: List[Dict[str, Any]]
    health: str

class RuntimeMessage(WSMessageBase):
    state: str
    total_frames_processed: int
    average_fps: float
    total_recognitions: int
    total_unknowns: int
    dropped_frames: int

class LogMessage(WSMessageBase):
    level: str
    component: str
    message: str
