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
        """Synchronous cv2 operations wrapped for async contexts."""
        # Use platform-native backends for lower capture overhead
        import sys
        api_preference = cv2.CAP_ANY
        if sys.platform.startswith('win'):
            api_preference = cv2.CAP_DSHOW
        elif sys.platform.startswith('linux'):
            api_preference = cv2.CAP_V4L2

        self.cap = await asyncio.to_thread(cv2.VideoCapture, self.config.camera_index, api_preference)
        
        if self.cap and self.cap.isOpened():
            # Enforce 1-frame driver-level buffer to ensure real-time retrieval
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Explicit FPS
            fps = self.config.target_fps or 30
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            
            # Explicit Resolution (Defaulting to 640x480)
            res = self.config.preferred_resolution or (640, 480)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, res[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res[1])

            if self.config.fourcc:
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.config.fourcc))
                
            self.health.is_connected = True
            logger.info(f"Webcam {self.config.camera_index} connected successfully (API={api_preference}, FPS={fps}, Res={res[0]}x{res[1]}).")
            return True
            
        self.health.last_error = f"Failed to open webcam {self.config.camera_index}"
        return False

    async def disconnect(self) -> None:
        self.running = False
        self.health.is_streaming = False
        if self.cap:
            await asyncio.to_thread(self.cap.release)
            self.cap = None
        self.health.is_connected = False

    def _capture_thread_func(self) -> None:
        logger.info(f"Webcam background thread starting on index {self.config.camera_index}")
        while self.running and self.cap and self.cap.isOpened():
            ret, image = self.cap.read()
            if not ret or image is None:
                time.sleep(0.01)
                continue
            self.latest_frame = image
        logger.info(f"Webcam background thread stopped for index {self.config.camera_index}")

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
        pass # Not natively supported by raw cv2 webcams

    async def resume(self) -> None:
        pass

    async def read_frame(self) -> Optional[Frame]:
        if not self.health.is_streaming:
            return None
            
        # Wait up to 500ms for a new frame
        for _ in range(50):
            image = self.latest_frame
            if image is not None:
                self.latest_frame = None  # Consume frame
                self.frame_counter += 1
                return Frame.create(
                    source_id=self.config.source_id,
                    image=image,
                    frame_number=self.frame_counter,
                    timestamp=time.time()
                )
            await asyncio.sleep(0.01)
            
        self.health.last_error = "Timeout waiting for new frame from webcam thread"
        return None
