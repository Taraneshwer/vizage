"""
Strongly typed Frame abstraction.
Isolates the AI pipeline from raw OpenCV numpy arrays.
"""
import numpy as np
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

class Frame(BaseModel):
    """
    Encapsulates a single video or image frame and its metadata.
    Every component in the application must consume this object instead of raw arrays.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    frame_id: str
    source_id: str
    timestamp: float
    image: np.ndarray
    width: int
    height: int
    channels: int
    fps: Optional[float] = None
    frame_number: int = 0
    color_space: str = "BGR"
    metadata: Dict[str, Any] = {}
    capture_latency_ms: float = 0.0
    processing_metadata: Dict[str, Any] = {}

    @property
    def data(self) -> np.ndarray:
        """Alias for compatibility with legacy components expecting raw image data."""
        return self.image
    
    @classmethod
    def create(cls, source_id: str, image: np.ndarray, frame_number: int, timestamp: float, metadata: Optional[Dict[str, Any]] = None) -> "Frame":
        """
        Helper to construct a Frame object from a raw numpy array.
        
        Args:
            source_id (str): The ID of the source.
            image (np.ndarray): The raw BGR image array.
            frame_number (int): Sequential frame index.
            timestamp (float): UNIX timestamp of capture.
            metadata (dict, optional): Additional source metadata.
            
        Returns:
            Frame: A strongly typed frame object.
        """
        h, w = image.shape[:2]
        c = image.shape[2] if len(image.shape) > 2 else 1
        
        return cls(
            frame_id=f"{source_id}_{frame_number}",
            source_id=source_id,
            timestamp=timestamp,
            image=image,
            width=w,
            height=h,
            channels=c,
            frame_number=frame_number,
            metadata=metadata or {}
        )
