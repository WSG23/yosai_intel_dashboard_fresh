"""Real-time analytics dashboard websocket implementation."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


router = APIRouter()


class AnalyticsEvent(BaseModel):
    """Schema for analytics events sent over the websocket."""

    timestamp: datetime
    type: str
    payload: dict[str, Any] | None = None


async def heartbeat_stream(
    interval: float = 30.0,
) -> AsyncGenerator[AnalyticsEvent, None]:
    """Yield heartbeat events at the given interval."""

    while True:
        event = AnalyticsEvent(
            timestamp=datetime.now(tz=timezone.utc),
            type="heartbeat",
        )
        yield event
        await asyncio.sleep(interval)


@router.websocket("/ws/analytics")
async def analytics_endpoint(websocket: WebSocket) -> None:
    """Websocket endpoint that streams analytics events to the client."""

    await websocket.accept()
    try:
        async for event in heartbeat_stream():
            await websocket.send_json(event.model_dump(mode="json"))
    except WebSocketDisconnect:
        pass
