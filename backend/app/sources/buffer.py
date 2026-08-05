"""
FrameBuffer abstraction for asynchronous, drop-aware frame queuing.
"""
import asyncio
from typing import Optional
from app.sources.frame import Frame
from loguru import logger

class FrameBuffer:
    """
    An asynchronous buffer for Frame objects.
    Handles overflow policies and drop strategies seamlessly.
    """
    def __init__(self, max_size: int = 30, drop_strategy: str = "oldest"):
        """
        Args:
            max_size (int): Maximum frames in the buffer.
            drop_strategy (str): 'oldest' or 'newest' when full.
        """
        self.max_size = max_size
        self.drop_strategy = drop_strategy
        self._queue: asyncio.Queue[Frame] = asyncio.Queue(maxsize=max_size)
        self.dropped_frames = 0
        self.total_enqueued = 0

    async def enqueue(self, frame: Frame) -> bool:
        """
        Asynchronously adds a frame to the buffer.
        If full, applies the drop strategy to maintain flow.
        
        Args:
            frame (Frame): The strongly typed frame object.
            
        Returns:
            bool: True if frame was kept, False if it was dropped (if strategy is newest).
        """
        if self._queue.full():
            self.dropped_frames += 1
            if self.drop_strategy == "oldest":
                try:
                    self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            elif self.drop_strategy == "newest":
                return False
                
        await self._queue.put(frame)
        self.total_enqueued += 1
        return True

    async def dequeue(self) -> Frame:
        """
        Asynchronously retrieves the next frame from the buffer.
        """
        return await self._queue.get()
        
    def dequeue_nowait(self) -> Optional[Frame]:
        """
        Synchronously retrieves the next frame if available, else None.
        """
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    def size(self) -> int:
        """Returns the current number of frames in the buffer."""
        return self._queue.qsize()
        
    def clear(self) -> None:
        """Empties the buffer."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
