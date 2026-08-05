"""
HTTP / MJPEG provider for IP Cameras.
"""
import asyncio
import time
import cv2
import httpx
import numpy as np
from typing import Optional
from app.sources.base import StreamingSource
from app.sources.schemas import IPCameraConfig, SourceCapabilities
from app.sources.frame import Frame
from app.sources.factory import SourceFactory
from loguru import logger

@SourceFactory.register("ip_camera")
class IPCameraSource(StreamingSource):
    """Provider for HTTP/MJPEG IP cameras."""
    def __init__(self, config: IPCameraConfig):
        super().__init__(config)
        self.config: IPCameraConfig = config
        self.client: Optional[httpx.AsyncClient] = None
        self.frame_counter = 0

    def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            supports_streaming=True,
            supports_snapshots=True,
            supports_reconnect=True,
            supports_pause=False
        )

    async def connect(self) -> bool:
        headers = {}
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        self.client = httpx.AsyncClient(headers=headers, timeout=self.config.connection_timeout_sec)
        # Note: True MJPEG streaming requires iterative reading.
        # For Milestone 1.5, we validate the endpoint can be reached.
        try:
            # We assume a snapshot endpoint for simplicity of the abstraction
            response = await self.client.head(self.config.http_url)
            if response.status_code < 400:
                self.health.is_connected = True
                logger.info(f"IP Camera {self.config.source_id} connected.")
                return True
        except Exception as e:
            self.health.last_error = str(e)
            logger.error(f"IP Camera connection failed: {e}")
            
        return False

    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
        self.health.is_connected = False
        self.health.is_streaming = False

    async def start(self) -> None:
        if not self.health.is_connected:
            await self.connect()
        self.health.is_streaming = True

    async def stop(self) -> None:
        self.health.is_streaming = False

    async def pause(self) -> None:
        pass

    async def resume(self) -> None:
        pass

    async def read_frame(self) -> Optional[Frame]:
        if not self.health.is_streaming or not self.client:
            return None
            
        try:
            # Simple snapshot approach; production would handle multipart/x-mixed-replace
            response = await self.client.get(self.config.http_url)
            if response.status_code == 200:
                np_arr = np.frombuffer(response.content, np.uint8)
                image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if image is not None:
                    self.frame_counter += 1
                    await asyncio.sleep(self.config.snapshot_interval_ms / 1000.0)
                    return Frame.create(
                        source_id=self.config.source_id,
                        image=image,
                        frame_number=self.frame_counter,
                        timestamp=time.time()
                    )
        except Exception as e:
            self.health.last_error = str(e)
            
        return None
