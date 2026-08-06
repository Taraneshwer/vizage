"""
ESP32-CAM HTTP provider.
"""
import asyncio
import time
import cv2
import httpx
import numpy as np
from typing import Optional
from app.sources.base import StreamingSource
from app.sources.schemas import ESP32Config, SourceCapabilities
from app.sources.frame import Frame
from app.sources.factory import SourceFactory
from loguru import logger

@SourceFactory.register("esp32")
class ESP32Source(StreamingSource):
    """Provider specifically tuned for ESP32-CAM microcontrollers."""
    def __init__(self, config: ESP32Config):
        super().__init__(config)
        self.config: ESP32Config = config
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
        self.client = httpx.AsyncClient(timeout=self.config.connection_timeout_sec)
        try:
                                                     
            base_url = self.config.stream_url.rsplit("/", 1)[0]
            await self.client.get(f"{base_url}/control?var=framesize&val={self.config.resolution_mode}")
            self.health.is_connected = True
            logger.info(f"ESP32-CAM {self.config.source_id} connected.")
            return True
        except Exception as e:
            self.health.last_error = str(e)
            logger.error(f"ESP32 connection failed: {e}")
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
                                            
            response = await self.client.get(self.config.stream_url)
            if response.status_code == 200:
                np_arr = np.frombuffer(response.content, np.uint8)
                image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if image is not None:
                    self.frame_counter += 1
                    return Frame.create(
                        source_id=self.config.source_id,
                        image=image,
                        frame_number=self.frame_counter,
                        timestamp=time.time()
                    )
        except Exception as e:
            self.health.last_error = str(e)
            
        return None
