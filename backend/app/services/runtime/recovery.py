"""
Error Recovery System.
Centralized exception handling for the runtime orchestrator to prevent crashes.
"""
from typing import Callable, Any
from app.core.logger import get_logger
from app.services.ai.gpu_manager import GPUManager
from app.core.events import EventBus, ErrorEvent

logger = get_logger(__name__)

class ErrorRecoveryManager:
    def __init__(self):
        self.gpu_manager = GPUManager()
        self.event_bus = EventBus()
        
    def handle_exception(self, e: Exception, source: str) -> None:
        """Determines recovery tactics based on the exception type."""
        error_msg = str(e)
        
                                    
        if "CUDA out of memory" in error_msg or "OOM" in error_msg.upper():
            logger.critical(f"GPU OOM detected in {source}. Initiating cache clear recovery.")
            self.gpu_manager.empty_cache()
            self.event_bus.publish_sync(ErrorEvent(source=source, error_msg="GPU OOM Detected. Cache cleared.", critical=True))
            return
            
                                   
        if "Connection" in error_msg or "Camera" in error_msg:
            logger.error(f"Camera failure in {source}. Dropping frame and expecting Runtime to reconnect.")
            self.event_bus.publish_sync(ErrorEvent(source=source, error_msg="Camera connection lost.", critical=False))
            return
            
                                    
        if "YOLO" in error_msg or "MediaPipe" in error_msg:
            logger.error(f"Model Inference failed in {source}: {e}")
            self.event_bus.publish_sync(ErrorEvent(source=source, error_msg=error_msg, critical=False))
            return
            
                             
        logger.error(f"Unhandled exception in {source}: {e}")
        self.event_bus.publish_sync(ErrorEvent(source=source, error_msg=error_msg, critical=True))
