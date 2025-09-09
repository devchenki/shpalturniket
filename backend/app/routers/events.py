"""
Router для событий (SSE)
"""

import asyncio
import json
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..utils.events_bus import event_manager


router = APIRouter()


@router.get("/events/stream", summary="Поток событий")
async def stream_events():
    """Поток событий в реальном времени"""

    async def event_generator():
        queue = await event_manager.subscribe()
        heartbeat_interval = 30
        last_heartbeat = 0
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=heartbeat_interval)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat
                    heartbeat = {
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {"status": "ok"},
                    }
                    yield f"data: {json.dumps(heartbeat)}\n\n"
        finally:
            await event_manager.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )
