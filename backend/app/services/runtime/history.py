"""
Structured History.
Defines models for persisting recognition events to the DB.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class RecognitionHistoryEntry(BaseModel):
    identity_id: str
    verification_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    camera_id: str
    pipeline_time_ms: float
    tracking_id: str
    similarity: float
    recognition_mode: str
    image_reference: Optional[str] = None # Path to saved image crop
