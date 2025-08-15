from __future__ import annotations

"""Reconciliation job for Timescale outbox events.

The job scans the ``outbox_events`` table and verifies that each payload has a
corresponding entry in ``access_events``.  Processed rows are marked and the
number of divergences is returned so that callers can emit metrics or alerts.
"""

from typing import Mapping

from yosai_intel_dashboard.src.services.timescale.manager import TimescaleDBManager


async def reconcile_outbox(manager: TimescaleDBManager) -> int:
    """Process outbox messages and detect divergences.

    Parameters
    ----------
    manager:
        Initialised :class:`TimescaleDBManager` instance.

    Returns
    -------
    int
        The number of outbox rows that lacked a corresponding access event.
    """

    await manager.connect()
    rows = await manager.unprocessed_outbox_events()
    divergences = 0
    assert manager.pool is not None
    async with manager.pool.acquire() as conn:
        for row in rows:
            payload: Mapping[str, object] = row["payload"]
            event_id = payload.get("event_id")
            exists = await conn.fetchval(
                "SELECT 1 FROM access_events WHERE event_id = $1", event_id
            )
            if exists:
                await manager.mark_outbox_processed(row["id"])
            else:
                divergences += 1
    return divergences
