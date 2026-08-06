"""
Enrollment Import Framework architecture.
Defines interfaces for importing frames from various sources into the enrollment pipeline.
"""
from abc import ABC, abstractmethod
from typing import List, AsyncGenerator
from app.sources.frame import Frame
from app.sources.manager import SourceManager
from loguru import logger

class IEnrollmentSource(ABC):
    """
    Interface for providing frames to the enrollment process.
    """
    @abstractmethod
    async def get_frames(self) -> AsyncGenerator[Frame, None]:
        """Yields frames for enrollment processing."""
        pass

class EnrollmentImportService:
    """
    Manages the ingestion of frames for enrollment from various underlying sources.
    """
    def __init__(self, source_manager: SourceManager):
        self.source_manager = source_manager

    async def import_from_stream(self, source_id: str, duration_sec: float) -> List[Frame]:
        """
        Captures a burst of frames from a live stream for enrollment.
        """
        import asyncio
        import time
        
        frames = []
        session = self.source_manager.get_session(source_id)
        if not session:
            logger.error(f"Cannot import from unknown stream {source_id}")
            return frames
            
        end_time = time.time() + duration_sec
        while time.time() < end_time:
            frame = await session.get_next_frame()
            if frame:
                frames.append(frame)
            else:
                await asyncio.sleep(0.01)
                
        return frames

    async def import_from_static(self, source_id: str) -> List[Frame]:
        """
        Imports frames from a static image source.
        """
        source = self.source_manager.static_sources.get(source_id)
        if not source:
            logger.error(f"Cannot import from unknown static source {source_id}")
            return []
            
        frame = await source.read_image()               
        return [frame] if frame else []
