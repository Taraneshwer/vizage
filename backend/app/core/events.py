"""
Application Event Bus.
Provides a strictly-typed Pub/Sub mechanism for decoupling orchestration from downstream consumers (e.g., logging, websockets).
"""
import asyncio
from typing import Callable, Dict, List, Any, Type, Awaitable
from pydantic import BaseModel, Field
from datetime import datetime
from app.core.logger import get_logger

logger = get_logger(__name__)

                 
class AppEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)

                      
class FrameCapturedEvent(AppEvent):
    camera_id: str
    frame_id: str

class RecognitionEvent(AppEvent):
    identity_id: str
    verification_score: float
    bbox: tuple                   
    camera_id: str
    frame_id: str
    tracking_id: str
    mask_status: bool
    recognition_mode: str                    
    processing_time_ms: float
    capture_timestamp: float

class UnknownDetectedEvent(AppEvent):
    camera_id: str
    frame_id: str
    tracking_id: str

class HistoryEvent(AppEvent):
    history_id: str
    timestamp: str
    identity_id: str = None
    name: str = None
    department: str = None
    verification_score: int
    mode: str
    camera_id: str
    tracking_id: str
    processing_time_ms: int
    state: str
    has_mask: bool

class CameraDisconnectedEvent(AppEvent):
    camera_id: str
    reason: str

class CameraRecoveredEvent(AppEvent):
    camera_id: str

class ErrorEvent(AppEvent):
    source: str
    error_msg: str
    critical: bool = False

import threading

                     
class EventBus:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._subscribers = {}
                cls._loop = None
            return cls._instance
        
    def _get_loop(self):
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
        return self._loop
        
    def subscribe(self, event_type: Type[AppEvent], callback: Callable[[AppEvent], Awaitable[None]]) -> None:
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
                                             
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                logger.debug(f"Subscribed {callback.__name__} to {event_type.__name__}")
        
    async def publish(self, event: AppEvent) -> None:
        event_type = type(event)
        callbacks = []
        with self._lock:
            if event_type in self._subscribers:
                callbacks = list(self._subscribers[event_type])                                
                
        if callbacks:
            tasks = [cb(event) for cb in callbacks]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
    def publish_sync(self, event: AppEvent) -> None:
        """Helper to fire-and-forget an event from synchronous code if a loop is running."""
        loop = self._get_loop()
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.publish(event), loop)
        else:
                                                        
            logger.warning(f"Cannot publish {type(event).__name__}: No running event loop found.")
