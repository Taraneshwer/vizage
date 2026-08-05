"""
SQLAlchemy database models.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from app.db.base import BaseModel

class Identity(BaseModel):
    """
    Enrolled identity in the system.
    """
    __tablename__ = "identities"

    identity_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    notes = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    recognition_count = Column(Integer, default=0)
    last_seen = Column(DateTime, nullable=True)

class RecognitionHistory(BaseModel):
    """
    Log of individual recognition events.
    """
    __tablename__ = "recognition_history"

    timestamp = Column(DateTime, nullable=False)
    identity_id = Column(String(255), index=True, nullable=True)
    name = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    verification_score = Column(Integer, nullable=False)
    mode = Column(String(50), nullable=False) # e.g. "Known", "Unknown"
    camera_id = Column(String(255), nullable=False)
    tracking_id = Column(String(255), nullable=True)
    processing_time_ms = Column(Integer, nullable=False)
    state = Column(String(50), nullable=False)
    has_mask = Column(Boolean, default=False)

class CameraSource(BaseModel):
    """
    Saved CCTV/IP Camera Configurations
    """
    __tablename__ = "camera_sources"

    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False) # e.g. "RTSP", "WEBCAM", "IPCAMERA"
    connection_url = Column(String(1024), nullable=False) # RTSP url or integer string for webcam index
    is_active = Column(Boolean, default=False)
