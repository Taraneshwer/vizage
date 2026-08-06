"""
Runtime Configuration.
Defines system-wide dynamic constraints and behavior settings.
"""
from pydantic import BaseModel

class RuntimeConfig(BaseModel):
    target_fps: int = 2
    max_frame_queue_size: int = 10
    camera_reconnect_delay_sec: float = 5.0
    batch_size: int = 1                  
    runtime_mode: str = "PRODUCTION"                      
    
                 
    theme: str = "Dark (Enterprise)"
    language: str = "English"
    confidence_threshold: float = 98.0
    tracking_strategy: str = "ByteTrack (High Accuracy)"
    default_source: str = "RTSP: Front Entrance"
    log_retention: str = "30 Days"
    save_unknown_faces: bool = True
    
    class Config:
        arbitrary_types_allowed = True

                                                             
app_runtime_config = RuntimeConfig()
