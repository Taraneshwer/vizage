"""
Static image file provider.
"""
import cv2
import asyncio
import time
from typing import Optional
from app.sources.base import StaticImageSource
from app.sources.schemas import ImageConfig, SourceCapabilities
from app.sources.frame import Frame
from app.sources.factory import SourceFactory
from loguru import logger

@SourceFactory.register("image")
class ImageSource(StaticImageSource):
    """Provider for single static image files."""
    def __init__(self, config: ImageConfig):
        super().__init__(config)
        self.config: ImageConfig = config
        self._cached_image: Optional[Frame] = None

    def get_capabilities(self) -> SourceCapabilities:
        return SourceCapabilities(
            supports_streaming=False,
            supports_snapshots=True,
            supports_reconnect=False,
            supports_pause=False
        )

    async def connect(self) -> bool:
        try:
            image = await asyncio.to_thread(cv2.imread, self.config.file_path)
            if image is not None:
                self.health.is_connected = True
                frame = Frame.create(
                    source_id=self.config.source_id,
                    image=image,
                    frame_number=1,
                    timestamp=time.time()
                )
                if self.config.cache_in_memory:
                    self._cached_image = frame
                logger.info(f"Image {self.config.source_id} loaded.")
                return True
        except Exception as e:
            self.health.last_error = str(e)
            logger.error(f"Failed to load image: {e}")
            
        return False

    async def disconnect(self) -> None:
        self._cached_image = None
        self.health.is_connected = False

    async def read_image(self) -> Optional[Frame]:
        if not self.health.is_connected:
            return None
            
        if self._cached_image is not None:
            return self._cached_image
            
                               
        image = await asyncio.to_thread(cv2.imread, self.config.file_path)
        if image is not None:
            return Frame.create(
                source_id=self.config.source_id,
                image=image,
                frame_number=1,
                timestamp=time.time()
            )
        return None
