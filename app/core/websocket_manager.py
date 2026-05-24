from typing import Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        # Maps session_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: session={session_id}")

    def disconnect(self, session_id: str) -> None:
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: session={session_id}")

    async def send_json(self, session_id: str, data: dict) -> None:
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json(data)
            except Exception:
                self.disconnect(session_id)

    async def send_bytes(self, session_id: str, data: bytes) -> None:
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_bytes(data)
            except Exception:
                self.disconnect(session_id)

    def is_connected(self, session_id: str) -> bool:
        return session_id in self.active_connections


# Single global instance shared across the app
ws_manager = WebSocketManager()