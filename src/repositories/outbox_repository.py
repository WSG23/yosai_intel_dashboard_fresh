from __future__ import annotations

"""Transactional outbox repository for access events.

This repository persists access events using the TimescaleDB manager.  Events
are written to the primary ``access_events`` table and an ``outbox_events``
queue in a single transaction so that downstream consumers can reliably
process them.
"""

from dataclasses import dataclass
from typing import Any, Mapping

from yosai_intel_dashboard.src.services.timescale.manager import TimescaleDBManager


@dataclass
class OutboxRepository:
    """Repository implementing the transactional outbox pattern."""

    manager: TimescaleDBManager

    async def save_access_event(self, event: Mapping[str, Any]) -> None:
        """Persist ``event`` to the database and enqueue it in the outbox."""

        await self.manager.record_access_event(dict(event))

    async def pending_events(self) -> int:
        """Return number of events waiting in the outbox."""

        return await self.manager.pending_outbox_events()

    async def unprocessed_events(self) -> list[Mapping[str, Any]]:
        """Fetch unprocessed outbox events."""

        return [dict(r) for r in await self.manager.unprocessed_outbox_events()]

    async def mark_processed(self, event_id: Any) -> None:
        """Mark a previously fetched event as processed."""

        await self.manager.mark_outbox_processed(event_id)
