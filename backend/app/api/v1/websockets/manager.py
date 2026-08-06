"""
WebSocket Streaming Manager.
Manages connections, broadcasting, backpressure, and graceful disconnects.
"""
import asyncio
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect
from app.core.logger import get_logger

logger = get_logger(__name__)

class StreamingManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StreamingManager, cls).__new__(cls)
                                         
            cls._instance.active_connections = {
                "recognition": [],
                "camera": [],
                "system": [],
                "runtime": [],
                "logs": [],
                "history": []
            }
        return cls._instance
        
    async def connect(self, websocket: WebSocket, topic: str):
        await websocket.accept()
        if topic not in self.active_connections:
            self.active_connections[topic] = []
        self.active_connections[topic].append(websocket)
        logger.debug(f"Client connected to WS topic: {topic}")
        
    def disconnect(self, websocket: WebSocket, topic: str):
        if topic in self.active_connections and websocket in self.active_connections[topic]:
            self.active_connections[topic].remove(websocket)
            logger.debug(f"Client disconnected from WS topic: {topic}")
            
    async def broadcast(self, topic: str, message: str):
        """
        Broadcasts a string (JSON) to all clients subscribed to a topic.
        Includes backpressure protection: if a client is too slow, it doesn't block others.
        """
        if topic not in self.active_connections or not self.active_connections[topic]:
            return
            
        dead_connections = []
        for connection in self.active_connections[topic]:
            try:
                                                                               
                await asyncio.wait_for(connection.send_text(message), timeout=1.0)
            except (WebSocketDisconnect, RuntimeError):
                dead_connections.append(connection)
            except asyncio.TimeoutError:
                logger.warning(f"Dropping slow WS client on {topic}")
                dead_connections.append(connection)
            except Exception as e:
                logger.error(f"WS Broadcast error on {topic}: {e}")
                dead_connections.append(connection)
                
                                   
        for dead in dead_connections:
            self.disconnect(dead, topic)
