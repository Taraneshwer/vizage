"""
WebSocket Routers.
Exposes streaming endpoints.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import asyncio
from app.api.v1.websockets.manager import StreamingManager

router = APIRouter(prefix="/ws", tags=["WebSockets"])

# Simple dependency to get manager
def get_manager():
    return StreamingManager()

@router.websocket("/recognition")
async def ws_recognition(websocket: WebSocket, manager: StreamingManager = Depends(get_manager)):
    await manager.connect(websocket, "recognition")
    try:
        while True:
            # Client heartbeat
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "recognition")

@router.websocket("/camera")
async def ws_camera(websocket: WebSocket, manager: StreamingManager = Depends(get_manager)):
    await manager.connect(websocket, "camera")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "camera")

@router.websocket("/system")
async def ws_system(websocket: WebSocket, manager: StreamingManager = Depends(get_manager)):
    await manager.connect(websocket, "system")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "system")

@router.websocket("/runtime")
async def ws_runtime(websocket: WebSocket, manager: StreamingManager = Depends(get_manager)):
    await manager.connect(websocket, "runtime")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "runtime")

@router.websocket("/logs")
async def ws_logs(websocket: WebSocket, manager: StreamingManager = Depends(get_manager)):
    await manager.connect(websocket, "logs")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "logs")

@router.websocket("/history")
async def ws_history(websocket: WebSocket, manager: StreamingManager = Depends(get_manager)):
    await manager.connect(websocket, "history")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "history")
