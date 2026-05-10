from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.services.progress import broadcaster

router = APIRouter()


@router.websocket("/ws/progress")
async def websocket_progress(ws: WebSocket):
    await broadcaster.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(ws)
