"""
Strongly typed models for the AI Core pipeline.
"""
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import numpy as np
from app.sources.frame import Frame

class RecognitionState(str, Enum):
    SEARCHING = "Searching"
    CANDIDATE_FOUND = "Candidate Found"
    VERIFYING = "Verifying"
    RECOGNIZED = "Recognized"
    TRACKING = "Tracking"
    LOST = "Lost"

class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int
    
    @property
    def width(self) -> int:
        return self.x2 - self.x1
        
    @property
    def height(self) -> int:
        return self.y2 - self.y1
        
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x1 + self.width // 2, self.y1 + self.height // 2)

class DetectionResult(BaseModel):
    bbox: BoundingBox
    confidence: float
    face_crop: Optional[np.ndarray] = Field(default=None, repr=False)
    tracking_id: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True

class MaskResult(BaseModel):
    has_mask: bool
    confidence: float

class LandmarkResult(BaseModel):
    landmarks: np.ndarray = Field(repr=False) # shape (N, 2) or (N, 3)
    aligned_face_crop: Optional[np.ndarray] = Field(default=None, repr=False)
    upper_face_crop: Optional[np.ndarray] = Field(default=None, repr=False)
    
    class Config:
        arbitrary_types_allowed = True

class Embedding(BaseModel):
    vector: np.ndarray = Field(repr=False) # shape (512,)
    model_version: str = "adaface_ir100"
    is_upper_face: bool = False
    
    class Config:
        arbitrary_types_allowed = True

class RecognitionCandidate(BaseModel):
    identity_id: str
    similarity_score: float # Distance or cosine similarity
    name: Optional[str] = None
    department: Optional[str] = None

class DecisionExplanation(BaseModel):
    reason: str
    embedding_score: float = 0.0
    temporal_stability: float = 0.0
    tracking_score: float = 0.0
    is_accepted: bool = False
    decision_type: str = "Unknown" # Known, Possible Match, Unknown, Reject

class RecognitionResult(BaseModel):
    detection: DetectionResult
    mask: Optional[MaskResult] = None
    landmarks: Optional[LandmarkResult] = None
    embedding: Optional[Embedding] = None
    candidate: Optional[RecognitionCandidate] = None
    tracking_id: Optional[str] = None
    is_unknown: bool = True
    
    # New Decision Engine fields
    verification_score: float = 0.0
    decision_explanation: Optional[DecisionExplanation] = None
    state: RecognitionState = RecognitionState.SEARCHING

class ModelStatus(BaseModel):
    name: str
    status: str # "Online", "Offline", "Error", "Loading"
    device: str
    backend: str
    vram_usage_mb: Optional[int] = None
    avg_inference_ms: Optional[float] = None
    error_message: Optional[str] = None

class GPUStatus(BaseModel):
    is_available: bool
    device_name: str
    total_memory_mb: int
    allocated_memory_mb: int
    free_memory_mb: int
    utilization_percent: Optional[float] = None
    temperature: Optional[float] = None

class RecognitionContext(BaseModel):
    """
    State object traversing the inference pipeline.
    """
    frame: Frame
    detections: List[RecognitionResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timing metrics
    timers: Dict[str, float] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

class RecognitionSessionStats(BaseModel):
    runtime_seconds: float
    frames_processed: int
    recognitions_count: int
    unknowns_count: int
    average_confidence: float
    average_processing_time_ms: float
    current_fps: float

class SystemHealth(BaseModel):
    gpu: GPUStatus
    models: List[ModelStatus]
    uptime_seconds: float
    fps: float
