"""
API Response and Request Schemas.
Utilizes Pydantic v2 for strong typing and validation.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

# --- GENERIC SCHEMAS ---
class BaseResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    
# --- RECOGNITION SCHEMAS ---
class BoundingBoxModel(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int
    
class RecognizedCandidateModel(BaseModel):
    identity_id: str
    similarity_score: float
    name: Optional[str] = None
    
class RecognitionResultModel(BaseModel):
    is_unknown: bool
    state: str
    verification_score: float
    candidate: Optional[RecognizedCandidateModel] = None
    bbox: Optional[BoundingBoxModel] = None
    tracking_id: Optional[str] = None
    has_mask: bool
    processing_time_ms: float

class BatchRecognitionResultModel(BaseResponse):
    results: List[RecognitionResultModel]

# --- ENROLLMENT SCHEMAS ---
class EnrollmentRequest(BaseModel):
    identity_id: str = Field(..., description="Unique ID for the person")
    name: str = Field(..., description="Full name")
    
class EnrollmentResponse(BaseResponse):
    identity_id: Optional[str] = None

class IdentityModel(BaseModel):
    identity_id: str
    name: str
    department: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    recognition_count: int
    last_seen: Optional[str] = None
    enrollment_date: str

class UpdateIdentityRequest(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    notes: Optional[str] = None

# --- CAMERA SCHEMAS ---
class CameraSourceModel(BaseModel):
    id: str
    name: str
    source_type: str
    connection_url: str
    is_active: bool
    created_at: str

class CameraSourceCreateRequest(BaseModel):
    name: str
    source_type: str = Field(..., description="e.g. RTSP, WEBCAM")
    connection_url: str

class CameraSourceUpdateRequest(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    connection_url: Optional[str] = None
    is_active: Optional[bool] = None

class CameraConnectionRequest(BaseModel):
    camera_id: str = Field(..., description="Unique ID for the camera source")
    source_uri: str = Field(..., description="URI for the camera (RTSP, /dev/video0, etc)")
    source_type: str = Field(..., description="Type of source (WebcamSource, RTSPCameraSource)")

class CameraStatusResponse(BaseResponse):
    camera_id: str
    is_active: bool
    uptime: float
    fps: float
    dropped_frames: int

# --- RUNTIME SCHEMAS ---
class RuntimeStatsResponse(BaseModel):
    state: str
    total_frames_processed: int
    total_recognitions: int
    total_unknowns: int
    errors: int
    uptime_seconds: float
    average_fps: float
    
# --- SYSTEM SCHEMAS ---
class GPUStatusModel(BaseModel):
    is_available: bool
    device_name: str
    total_memory_mb: int
    allocated_memory_mb: int
    free_memory_mb: int
    
class SystemHealthResponse(BaseModel):
    health: str
    gpu: GPUStatusModel
    models: List[Dict[str, Any]]
    system: Dict[str, Any]
