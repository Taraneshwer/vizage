"""
Event Bridge.
Subscribes to internal EventBus and forwards to WebSocket StreamingManager.
"""
import asyncio
import time
import base64
import cv2
from app.core.events import EventBus, RecognitionEvent, FrameCapturedEvent, HistoryEvent
from app.api.v1.websockets.manager import StreamingManager
from app.api.v1.websockets.schemas import RecognitionStreamMessage, CameraFrameMessage, HistoryStreamMessage

class EventBridge:
    def __init__(self, event_bus: EventBus, manager: StreamingManager):
        self.event_bus = event_bus
        self.manager = manager
        
        # Subscribe to internal events
        self.event_bus.subscribe(RecognitionEvent, self._handle_recognition)
        self.event_bus.subscribe(HistoryEvent, self._handle_history)
        
        # Note: In a production system, we might want to bypass EventBus for raw frames
        # and tap directly into CameraRuntime to save memory, but we'll try this first if
        # frames are sent through EventBus, or we can use a callback.
        
    async def _handle_recognition(self, event: RecognitionEvent):
        # Translate to WS schema
        msg = RecognitionStreamMessage(
            topic="recognition",
            timestamp=time.time(),
            identity_id=event.identity_id,
            verification_score=event.verification_score,
            bbox=list(event.bbox),
            tracking_id=event.tracking_id,
            mask_status=event.mask_status,
            recognition_mode=event.recognition_mode,
            processing_time_ms=event.processing_time_ms,
            capture_timestamp=event.capture_timestamp
        )
        
        await self.manager.broadcast("recognition", msg.model_dump_json())
        
    async def _handle_history(self, event: HistoryEvent):
        msg = HistoryStreamMessage(
            topic="history",
            timestamp=time.time(),
            history_id=event.history_id,
            event_timestamp=event.timestamp,
            identity_id=event.identity_id,
            name=event.name,
            department=event.department,
            verification_score=event.verification_score,
            mode=event.mode,
            camera_id=event.camera_id,
            tracking_id=event.tracking_id,
            processing_time_ms=event.processing_time_ms,
            state=event.state,
            has_mask=event.has_mask
        )
        await self.manager.broadcast("history", msg.model_dump_json())

    async def broadcast_camera_frame(self, camera_id: str, frame_id: str, image_matrix, capture_timestamp: float = 0.0):
        """Called directly by CameraRuntime or Orchestrator to avoid EventBus memory bloat."""
        # Encode to JPEG
        # Optimization: only encode if there are active connections
        if not self.manager.active_connections.get("camera"):
            return
            
        success, buffer = cv2.imencode('.jpg', image_matrix, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if not success:
            return
            
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        
        msg = CameraFrameMessage(
            topic="camera",
            timestamp=time.time(),
            frame_id=frame_id,
            camera_id=camera_id,
            image_base64=jpg_as_text,
            capture_timestamp=capture_timestamp
        )
        
        await self.manager.broadcast("camera", msg.model_dump_json())
