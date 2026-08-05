"""
Abstract base class for the Universal Input Source Framework.
Every source (Webcam, RTSP, Video, ESP32) must implement this strict interface.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import numpy as np

class InputSource(ABC):
    """
    Abstract representation of any video or image source.
    The recognition pipeline consumes this interface without knowing the source type.
    """
    def __init__(self, source_uri: str, **kwargs):
        self.source_uri = source_uri
        self.config = kwargs
        self.is_connected = False
        self.is_streaming = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establishes connection to the source."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Cleans up resources and disconnects."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Starts the stream or background thread if required."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops the stream."""
        pass

    @abstractmethod
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Returns the next frame as a numpy array (BGR format for OpenCV compatibility).
        Returns None if no frame is available or stream ended.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns source metadata (e.g., fps, resolution, connection status).
        """
        pass
