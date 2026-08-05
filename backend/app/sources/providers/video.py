"""
Video file playback provider.
"""
import cv2
import asyncio
import time
from typing import Optional
from app.sources.base import StreamingSource
from app.sources.schemas import VideoConfig, SourceCapabilities
from app.sources.frame import Frame
from app.sources.factory import SourceFactory
from loguru import logger

@SourceFactory.register("video")
class VideoSource(StreamingSource):
    """Provider for local video files (MP4, AVI, MKV)."""
    def __init__(self, config: VideoConfig):
        super().__init__(config)
        self.config: VideoConfig = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_counter = 0
        self.video_fps = 30.0
        self._is_paused = False

    def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            supports_streaming=True,
            supports_snapshots=False,
            supports_reconnect=False,
            supports_pause=True,
            supports_looping=True,
            supports_seek=True
        )

    async def connect(self) -> bool:
        self.cap = await asyncio.to_thread(cv2.VideoCapture, self.config.file_path)
        if self.cap and self.cap.isOpened():
            self.video_fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
            self.health.is_connected = True
            logger.info(f"Video {self.config.source_id} loaded.")
            return True
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
        self._is_paused = False

    async def stop(self) -> None:
        self.health.is_streaming = False

    async def pause(self) -> None:
        self._is_paused = True

    async def resume(self) -> None:
        self._is_paused = False

    async def read_frame(self) -> Optional[Frame]:
        if not self.health.is_streaming or not self.cap:
            return None
            
        while self._is_paused:
            await asyncio.sleep(0.1)
            if not self.health.is_streaming:
                return None

        ret, image = await asyncio.to_thread(self.cap.read)
        if not ret or image is None:
            if self.config.loop:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, image = await asyncio.to_thread(self.cap.read)
            else:
                self.health.is_streaming = False
                return None

        self.frame_counter += 1
        
        if self.config.realtime_playback:
            await asyncio.sleep(1.0 / self.video_fps)
            
        return Frame.create(
            source_id=self.config.source_id,
            image=image,
            frame_number=self.frame_counter,
            timestamp=time.time()
        )
