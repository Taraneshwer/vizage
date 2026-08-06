"""
RTSP provider utilizing OpenCV.
"""
import cv2
import asyncio
import time
from typing import Optional
from app.sources.base import StreamingSource
from app.sources.schemas import RTSPConfig, SourceCapabilities
from app.sources.frame import Frame
from app.sources.factory import SourceFactory
from loguru import logger

@SourceFactory.register("rtsp")
class RTSPSource(StreamingSource):
    """Provider for network RTSP cameras (e.g. CCTV, IP Cameras)."""
    def __init__(self, config: RTSPConfig):
        super().__init__(config)
        self.config: RTSPConfig = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_counter = 0
        self.latest_frame = None
        self.capture_thread = None
        self.running = False

    def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            supports_streaming=True,
            supports_snapshots=True,
            supports_reconnect=True,
            supports_pause=False
        )

    async def connect(self) -> bool:
        if self.config.use_tcp:
                                                        
            import os
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
            
        self.cap = await asyncio.to_thread(cv2.VideoCapture, self.config.rtsp_url, cv2.CAP_FFMPEG)
        if self.cap and self.cap.isOpened():
            self.health.is_connected = True
            logger.info(f"RTSP stream {self.config.source_id} connected.")
            return True
        return False

    async def disconnect(self) -> None:
        self.running = False
        self.health.is_streaming = False
        if self.cap:
            await asyncio.to_thread(self.cap.release)
            self.cap = None
        self.health.is_connected = False

    def _capture_thread_func(self) -> None:
        logger.info(f"RTSP background thread starting on url {self.config.rtsp_url}")
        while self.running and self.cap and self.cap.isOpened():
            ret, image = self.cap.read()
            if not ret or image is None:
                time.sleep(0.01)
                continue
            self.latest_frame = image
        logger.info(f"RTSP background thread stopped for url {self.config.rtsp_url}")

    async def start(self) -> None:
        if not self.health.is_connected:
            await self.connect()
        self.health.is_streaming = True
        self.running = True
        self.latest_frame = None
        
        import threading
        self.capture_thread = threading.Thread(target=self._capture_thread_func, daemon=True)
        self.capture_thread.start()

    async def stop(self) -> None:
        self.health.is_streaming = False
        self.running = False

    async def pause(self) -> None:
        pass

    async def resume(self) -> None:
        pass

    async def read_frame(self) -> Optional[Frame]:
        if not self.health.is_streaming:
            return None
            
                                          
        for _ in range(50):
            image = self.latest_frame
            if image is not None:
                self.latest_frame = None                 
                self.frame_counter += 1
                return Frame.create(
                    source_id=self.config.source_id,
                    image=image,
                    frame_number=self.frame_counter,
                    timestamp=time.time()
                )
            await asyncio.sleep(0.01)
            
        self.health.last_error = "Timeout waiting for new frame from RTSP thread"
        return None
