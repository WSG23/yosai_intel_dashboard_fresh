"""Real-time analytics event streaming for the dashboard."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


class AnalyticsEvent(BaseModel):
    """Schema for analytics events sent to the client."""

    type: str
    payload: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


router = APIRouter(prefix="/real-time", tags=["analytics"])


async def _heartbeat_stream() -> AsyncIterator[str]:
    """Yield heartbeat events indefinitely."""

    while True:
        event = AnalyticsEvent(type="heartbeat")
        yield f"data: {event.model_dump_json()}\n\n"
        await asyncio.sleep(5)


@router.get("/events", response_class=StreamingResponse)
async def stream_events() -> StreamingResponse:
    """Stream analytics events to the client with periodic heartbeats."""

    return StreamingResponse(_heartbeat_stream(), media_type="text/event-stream")


__all__ = ["AnalyticsEvent", "router", "stream_events"]
