"""
Configuration, Capabilities, and Health schemas for the Universal Source Framework.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime

class SourceCapabilities(BaseModel):
    """Capabilities exposed by a source provider."""
    supports_streaming: bool = False
    supports_snapshots: bool = False
    supports_audio: bool = False
    supports_reconnect: bool = False
    supports_pause: bool = False
    supports_seek: bool = False
    supports_looping: bool = False
    supports_multiple_clients: bool = False

class SourceHealth(BaseModel):
    """Detailed health and performance metrics for a source."""
    is_connected: bool = False
    is_streaming: bool = False
    fps: float = 0.0
    resolution: tuple[int, int] = (0, 0)
    latency_ms: float = 0.0
    dropped_frames: int = 0
    reconnect_count: int = 0
    last_error: Optional[str] = None
    last_health_check: datetime = Field(default_factory=datetime.utcnow)
    
    # New metrics
    current_queue_size: int = 0
    average_latency_ms: float = 0.0
    last_frame_timestamp: Optional[float] = None
    average_fps: float = 0.0
    reconnect_attempts: int = 0
    uptime_seconds: float = 0.0
    dropped_frame_percentage: float = 0.0
    total_frames_received: int = 0
    total_frames_processed: int = 0

class BaseSourceConfig(BaseModel):
    """Base configuration for any input source."""
    source_id: str
    
    # Connection / Reconnect policies
    automatic_reconnect: bool = True
    reconnect_interval_sec: float = 5.0
    max_reconnect_attempts: int = -1  # -1 for infinite
    connection_timeout_sec: float = 10.0
    retry_policy: Literal["exponential", "fixed"] = "fixed"
    
    # Buffering
    frame_buffer_size: int = 2
    drop_strategy: Literal["oldest", "newest"] = "oldest"
    
    # Target Metrics
    target_fps: Optional[int] = None
    target_latency_ms: Optional[float] = None
    preferred_resolution: Optional[tuple[int, int]] = None
    preferred_codec: Optional[str] = None

class WebcamConfig(BaseSourceConfig):
    camera_index: int = 0
    fourcc: Optional[str] = "MJPG"

class RTSPConfig(BaseSourceConfig):
    rtsp_url: str
    use_tcp: bool = True

class IPCameraConfig(BaseSourceConfig):
    http_url: str
    auth_token: Optional[str] = None
    snapshot_interval_ms: int = 33

class ESP32Config(BaseSourceConfig):
    stream_url: str
    flashlight_enabled: bool = False
    resolution_mode: int = 9

class VideoConfig(BaseSourceConfig):
    file_path: str
    loop: bool = False
    realtime_playback: bool = True

class ImageConfig(BaseSourceConfig):
    file_path: str
    cache_in_memory: bool = True
