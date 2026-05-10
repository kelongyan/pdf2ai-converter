import asyncio
import json
from typing import Set
from fastapi import WebSocket


class ProgressBroadcaster:
    def __init__(self):
        self._connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws: WebSocket):
        self._connections.discard(ws)

    async def broadcast(self, task_id: str, event_type: str, data: dict):
        message = json.dumps({"type": event_type, "task_id": task_id, "data": data})
        dead = set()
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        self._connections -= dead


broadcaster = ProgressBroadcaster()
