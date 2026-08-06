"""
Source Session managing the asynchronous runtime lifecycle and buffering.
"""
import asyncio
import time
from typing import Optional, Dict, Any
from app.sources.base import StreamingSource
from app.sources.schemas import SourceHealth
from app.sources.buffer import FrameBuffer
from app.sources.frame import Frame
from loguru import logger

class SourceSession:
    """
    Wraps a StreamingSource to handle completely asynchronous frame queuing.
    Isolated from AI logic; acts only as a robust frame provider.
    """
    def __init__(self, source: StreamingSource):
        self.source = source
        self.buffer = FrameBuffer(
            max_size=source.config.frame_buffer_size,
            drop_strategy=source.config.drop_strategy
        )
        self.is_active = False
        self.start_time = 0.0
        self._capture_task: Optional[asyncio.Task] = None

    async def start_session(self) -> None:
        """Starts the source and the internal async capture loop."""
        self.is_active = True
        self.start_time = time.time()
        await self.source.start()
        
        # Launch the asynchronous capture loop
        self._capture_task = asyncio.create_task(self._capture_loop())
        logger.info(f"SourceSession started for {self.source.config.source_id}")

    async def stop_session(self) -> None:
        """Stops the source and cancels the capture loop."""
        self.is_active = False
        if self._capture_task:
            self._capture_task.cancel()
        await self.source.stop()
        await self.source.disconnect()
        logger.info(f"SourceSession stopped for {self.source.config.source_id}")

    async def _capture_loop(self) -> None:
        """
        Internal loop continuously reading frames asynchronously and buffering them.
        """
        try:
            while self.is_active:
                frame = await self.source.read_frame()
                if frame:
                    await self.buffer.enqueue(frame)
                    
                    # Update real-time health stats
                    self.source.health.last_frame_timestamp = frame.timestamp
                    self.source.health.total_frames_received += 1
                else:
                    await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in capture loop for {self.source.config.source_id}: {e}")
            self.source.health.last_error = str(e)

    async def get_next_frame(self) -> Frame:
        """
        Asynchronously retrieves the latest available frame from the buffer,
        discarding older intermediate frames to eliminate pipeline backlog.
        """
        # Wait until at least one frame is available
        frame = await self.buffer.dequeue()
        
        # Drain all remaining queued frames to get the absolute newest frame
        discarded_count = 0
        while True:
            next_frame = self.buffer.dequeue_nowait()
            if next_frame is None:
                break
            discarded_count += 1
            frame = next_frame
            
        if discarded_count > 0:
            self.buffer.dropped_frames += discarded_count
            
        self.source.health.total_frames_processed += 1
        return frame

    def get_session_stats(self) -> dict:
        """Aggregates buffer and source health metrics."""
        uptime = time.time() - self.start_time if self.is_active else 0
        health = self.source.get_health()
        
        health.uptime_seconds = uptime
        health.current_queue_size = self.buffer.size()
        health.dropped_frames = self.buffer.dropped_frames
        
        if health.total_frames_received > 0:
            health.dropped_frame_percentage = (health.dropped_frames / health.total_frames_received) * 100
            health.average_fps = health.total_frames_received / uptime if uptime > 0 else 0
            
        return health.model_dump()
