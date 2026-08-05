"""
Webcam provider utilizing OpenCV for local USB/Integrated cameras.
"""
import cv2
import asyncio
import time
from typing import Optional
from app.sources.base import StreamingSource
from app.sources.schemas import WebcamConfig, SourceCapabilities
from app.sources.frame import Frame
from app.sources.factory import SourceFactory
from loguru import logger

@SourceFactory.register("webcam")
class WebcamSource(StreamingSource):
    """Provider for local USB or integrated webcams."""
    def __init__(self, config: WebcamConfig):
        super().__init__(config)
        self.config: WebcamConfig = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_counter = 0

    def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            supports_streaming=True,
            supports_snapshots=True,
            supports_reconnect=True,
            supports_pause=False
        )

    async def connect(self) -> bool:
        """Synchronous cv2 operations wrapped for async contexts."""
        # Run cv2 blocking call in a thread pool to avoid blocking the event loop
        self.cap = await asyncio.to_thread(cv2.VideoCapture, self.config.camera_index)
        
        if self.cap and self.cap.isOpened():
            if self.config.fourcc:
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.config.fourcc))
            if self.config.width:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            if self.config.height:
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
                
            self.health.is_connected = True
            logger.info(f"Webcam {self.config.camera_index} connected successfully.")
            return True
            
        self.health.last_error = f"Failed to open webcam {self.config.camera_index}"
        return False

    async def disconnect(self) -> None:
        if self.cap:
            await asyncio.to_thread(self.cap.release)
        self.health.is_connected = False
        self.health.is_streaming = False

    async def start(self) -> None:
        if not self.health.is_connected:
            await self.connect()
        self.health.is_streaming = True

    async def stop(self) -> None:
        self.health.is_streaming = False

    async def pause(self) -> None:
        pass # Not natively supported by raw cv2 webcams

    async def resume(self) -> None:
        pass

    async def read_frame(self) -> Optional[Frame]:
        if not self.health.is_streaming or not self.cap:
            return None
            
        ret, image = await asyncio.to_thread(self.cap.read)
        if not ret or image is None:
            self.health.last_error = "Failed to grab frame from webcam"
            return None
            
        self.frame_counter += 1
        return Frame.create(
            source_id=self.config.source_id,
            image=image,
            frame_number=self.frame_counter,
            timestamp=time.time()
        )
