"""
Source Manager controlling multiple active sessions and full lifecycle operations.
"""
from typing import Dict, Optional, List
from app.sources.base import BaseSource, StreamingSource
from app.sources.session import SourceSession
from app.sources.factory import SourceFactory
from app.sources.schemas import BaseSourceConfig
from loguru import logger
import asyncio

class SourceManager:
    """
    Central orchestrator for all input sources.
    Handles startup, shutdown, pause, resume, and health aggregations.
    """
    def __init__(self):
        self.sessions: Dict[str, SourceSession] = {}
        self.static_sources: Dict[str, BaseSource] = {}

    async def add_streaming_source(self, source_type: str, config: BaseSourceConfig) -> SourceSession:
        source = SourceFactory.create(source_type, config)
        if not isinstance(source, StreamingSource):
            raise TypeError(f"Source type {source_type} is not a StreamingSource.")
            
        if not await source.connect():
            raise ConnectionError(f"Failed to connect to source {config.source_id}")
            
        session = SourceSession(source)
        await session.start_session()
        self.sessions[config.source_id] = session
        return session

    async def pause(self, source_id: str) -> None:
        """Pauses the stream if supported."""
        if session := self.sessions.get(source_id):
            if session.source.get_capabilities().supports_pause:
                await session.source.pause()
                logger.info(f"Paused source {source_id}")

    async def resume(self, source_id: str) -> None:
        """Resumes a paused stream."""
        if session := self.sessions.get(source_id):
            if session.source.get_capabilities().supports_pause:
                await session.source.resume()
                logger.info(f"Resumed source {source_id}")

    async def restart(self, source_id: str) -> None:
        """Restarts a streaming session completely."""
        if session := self.sessions.get(source_id):
            await session.stop_session()
            await session.start_session()
            logger.info(f"Restarted source {source_id}")

    async def reconnect(self, source_id: str) -> bool:
        """Forces a disconnect and reconnect on the underlying provider."""
        if session := self.sessions.get(source_id):
            await session.source.disconnect()
            connected = await session.source.connect()
            logger.info(f"Reconnected source {source_id}: {connected}")
            return connected
        return False

    async def shutdown_all(self) -> None:
        """Gracefully shuts down all active sessions and connections."""
        for s_id, session in self.sessions.items():
            await session.stop_session()
            await session.source.disconnect()
        for s_id, static_src in self.static_sources.items():
            await static_src.disconnect()
        self.sessions.clear()
        self.static_sources.clear()
        logger.info("All sources gracefully shut down.")

    def health_check(self) -> Dict[str, dict]:
        """Aggregates health status of all sources for the System Dashboard."""
        health_data = {}
        for s_id, session in self.sessions.items():
            health_data[s_id] = session.get_session_stats()
        for s_id, static_src in self.static_sources.items():
            health_data[s_id] = static_src.get_health().model_dump()
        return health_data
