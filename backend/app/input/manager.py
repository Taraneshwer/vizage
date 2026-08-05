"""
Manages active input sources across the application.
"""
from typing import Dict, Optional
from app.input.base import InputSource
from app.input.factory import InputSourceFactory
from loguru import logger

class InputManager:
    """
    Lifecycle manager for active input sources.
    """
    def __init__(self):
        self.active_sources: Dict[str, InputSource] = {}

    async def create_and_start(self, source_id: str, source_type: str, source_uri: str, **kwargs) -> InputSource:
        """Creates, connects, and starts a new source."""
        if source_id in self.active_sources:
            await self.stop_source(source_id)
            
        source = InputSourceFactory.create(source_type, source_uri, **kwargs)
        
        connected = await source.connect()
        if not connected:
            raise RuntimeError(f"Failed to connect to source {source_uri}")
            
        source.start()
        self.active_sources[source_id] = source
        logger.info(f"Started input source {source_id} ({source_type})")
        return source

    async def stop_source(self, source_id: str) -> None:
        """Stops and disconnects a source by ID."""
        if source_id in self.active_sources:
            source = self.active_sources.pop(source_id)
            source.stop()
            await source.disconnect()
            logger.info(f"Stopped input source {source_id}")

    def get_source(self, source_id: str) -> Optional[InputSource]:
        return self.active_sources.get(source_id)
