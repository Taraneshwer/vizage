"""
Hierarchy of abstract sources ensuring strict decoupled interfaces.
"""
from abc import ABC, abstractmethod
from typing import Optional, Any
from app.sources.schemas import SourceHealth, BaseSourceConfig, SourceCapabilities
from app.sources.frame import Frame

class BaseSource(ABC):
    """
    The absolute root for any data provider.
    """
    def __init__(self, config: BaseSourceConfig):
        self.config = config
        self.health = SourceHealth()

    @abstractmethod
    def get_capabilities(self) -> SourceCapabilities:
        """Returns the capabilities of the specific source provider."""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """Establishes connection to the source asynchronously."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Cleans up resources and disconnects asynchronously."""
        pass

    def get_health(self) -> SourceHealth:
        """Returns the aggregated health metrics for the source."""
        return self.health

class StreamingSource(BaseSource):
    """
    Abstract source for continuous video streams (Webcam, RTSP, Video).
    """
    @abstractmethod
    async def start(self) -> None:
        """Starts the asynchronous stream acquisition."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stops the asynchronous stream acquisition."""
        pass

    @abstractmethod
    async def pause(self) -> None:
        """Pauses the stream if supported."""
        pass

    @abstractmethod
    async def resume(self) -> None:
        """Resumes a paused stream."""
        pass

    @abstractmethod
    async def read_frame(self) -> Optional[Frame]:
        """
        Asynchronously reads the next frame, wrapping it in the Frame abstraction.
        Returns None if stream ended or disconnected.
        """
        pass

class StaticImageSource(BaseSource):
    """
    Abstract source for single-shot or batch static images.
    """
    @abstractmethod
    async def read_image(self) -> Optional[Frame]:
        """
        Reads a static image asynchronously and wraps it in a Frame.
        """
        pass
