from __future__ import annotations

"""Utilities for converting tabular records into access event collections."""

import logging
from datetime import datetime
from typing import Any, List

try:  # optional pandas dependency
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - fallback when pandas unavailable
    pd = None  # type: ignore

from yosai_intel_dashboard.src.core.domain.entities.events import AccessEvent
from yosai_intel_dashboard.src.core.domain.value_objects.enums import AccessResult, BadgeStatus

logger = logging.getLogger(__name__)


def dataframe_to_events(df: Any) -> List[AccessEvent]:
    """Convert a table-like object to ``AccessEvent`` instances.

    The adapter expects ``df`` to provide a ``to_dict('records')`` method and an
    ``empty`` attribute similar to :class:`pandas.DataFrame`.  Pandas is only
    required if timestamp values are provided as ``pd.Timestamp`` objects.
    """

    events: List[AccessEvent] = []
    if df is None or getattr(df, "empty", True):
        logger.warning("Empty DataFrame provided to AccessEvent adapter")
        return events

    try:
        records = df.to_dict("records")  # type: ignore[call-arg]
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Error accessing DataFrame records: %s", exc)
        return events

    for row in records:
        try:
            ts = row.get("timestamp")
            if (
                pd is not None
                and hasattr(pd, "Timestamp")
                and isinstance(ts, pd.Timestamp)  # type: ignore[attr-defined]
            ):
                timestamp = ts.to_pydatetime()
            else:
                try:
                    timestamp = datetime.fromisoformat(str(ts))
                except Exception:
                    timestamp = datetime.now()

            event = AccessEvent(
                event_id=str(row.get("event_id", "")),
                timestamp=timestamp,
                person_id=str(row.get("person_id") or row.get("user_id", "")),
                door_id=str(row.get("door_id") or row.get("location", "")),
                badge_id=row.get("badge_id"),
                access_result=AccessResult(row.get("access_result", AccessResult.DENIED.value)),
                badge_status=BadgeStatus(row.get("badge_status", BadgeStatus.INVALID.value)),
                door_held_open_time=float(row.get("door_held_open_time", 0.0)),
                entry_without_badge=bool(row.get("entry_without_badge", False)),
                device_status=row.get("device_status", "normal"),
                raw_data=row,
            )
            events.append(event)
        except Exception as exc:  # pragma: no cover - best effort per row
            logger.error("Error parsing access event row: %s", exc)

    return events


__all__ = ["dataframe_to_events"]
