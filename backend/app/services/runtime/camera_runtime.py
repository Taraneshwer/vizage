"""
Camera Runtime.
Orchestrates the input source session, manages callbacks, and handles auto-reconnects.
"""
import asyncio
import time
from typing import Optional, Callable
from app.core.logger import get_logger
from app.sources.session import SourceSession
from app.sources.base import StreamingSource
from app.core.runtime_config import app_runtime_config
from app.core.events import EventBus, FrameCapturedEvent, CameraDisconnectedEvent, CameraRecoveredEvent
from app.sources.frame import Frame

logger = get_logger(__name__)

class CameraRuntime:
    def __init__(self, camera_id: str, source: StreamingSource):
        self.camera_id = camera_id
        self.source = source
        self.session: Optional[SourceSession] = None
        self.event_bus = EventBus()
        self.is_running = False
        self._frame_callback: Optional[Callable[[Frame], None]] = None
        
    def set_callback(self, callback: Callable[[Frame], None]):
        """Sets the callback for when a frame is ready."""
        self._frame_callback = callback
        
    async def start(self) -> None:
        """Starts the camera runtime loop with auto-reconnect logic."""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info(f"Starting CameraRuntime for {self.camera_id}...")
        
        while self.is_running:
            try:
                # Initialize session
                self.session = SourceSession(self.source)
                await self.session.start_session()
                logger.info(f"CameraRuntime {self.camera_id} connected.")
                await self.event_bus.publish(CameraRecoveredEvent(camera_id=self.camera_id))
                
                # Frame loop
                frame_interval = 1.0 / app_runtime_config.target_fps
                
                while self.is_running:
                    loop_start = time.time()
                    
                    frame = await self.session.get_next_frame()
                    if frame is None:
                        if not self.session.is_active:
                            logger.warning(f"Failed to read frame from {self.camera_id}. Connection lost?")
                            break
                        else:
                            break
                        
                    # Publish event
                    await self.event_bus.publish(FrameCapturedEvent(
                        camera_id=self.camera_id,
                        frame_id=frame.frame_id
                    ))
                    
                    # Execute callback (Orchestrator)
                    if self._frame_callback:
                        self._frame_callback(frame)
                        
                    # Manage FPS
                    elapsed = time.time() - loop_start
                    sleep_time = frame_interval - elapsed
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                    else:
                        await asyncio.sleep(0.001) # Yield to event loop
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"CameraRuntime {self.camera_id} crashed: {e}")
                
            finally:
                if self.session:
                    await self.session.stop_session()
                    self.session = None
                    
            if self.is_running:
                logger.warning(f"Reconnecting CameraRuntime {self.camera_id} in {app_runtime_config.camera_reconnect_delay_sec}s...")
                await self.event_bus.publish(CameraDisconnectedEvent(camera_id=self.camera_id, reason="Connection dropped"))
                await asyncio.sleep(app_runtime_config.camera_reconnect_delay_sec)
                
    async def stop(self) -> None:
        """Gracefully shuts down the runtime."""
        if not self.is_running:
            return
            
        logger.info(f"Initiating graceful shutdown for CameraRuntime {self.camera_id}...")
        self.is_running = False
        
        if self.session:
            await self.session.stop_session()
            self.session = None
            
        logger.info(f"CameraRuntime {self.camera_id} stopped cleanly.")
