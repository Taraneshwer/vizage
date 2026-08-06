"""
Loguru Custom Sink for WebSocket Streaming.
"""
import asyncio
import time
from app.api.v1.websockets.manager import StreamingManager
from app.api.v1.websockets.schemas import LogMessage
import json

class WebSocketLogSink:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.manager = StreamingManager()
        self.loop = loop
        
    def write(self, message):
        """Called synchronously by Loguru"""
        record = message.record
        
                       
        payload = LogMessage(
            topic="logs",
            timestamp=time.time(),
            level=record["level"].name,
            component=record["name"],
            message=record["message"]
        )
        
                                           
        asyncio.run_coroutine_threadsafe(
            self.manager.broadcast("logs", payload.model_dump_json()),
            self.loop
        )
