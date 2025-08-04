from __future__ import annotations

"""Environmental data utilities.

This module centralises ETL routines for weather data along with connectors
for additional contextual signals such as social media and local event feeds.
The exposed helpers make it easy to merge these heterogeneous sources and to
correlate them with access logs for downstream analytics.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Iterable, List, Protocol, Sequence, Tuple

import pandas as pd

from yosai_intel_dashboard.src.database.protocols import ConnectionProtocol


# ---------------------------------------------------------------------------
# Weather ETL
# ---------------------------------------------------------------------------


@dataclass
class WeatherEvent:
    """Normalized weather metrics for storage and analysis."""

    timestamp: datetime
    temperature: float
    humidity: float
    precipitation: float
    wind: float
    visibility: float
    pressure: float
    lightning: bool


class WeatherClient(Protocol):
    """Protocol for weather data providers."""

    def fetch(self) -> dict:
        ...


def normalize(raw: dict) -> WeatherEvent:
    """Normalize a raw weather payload into :class:`WeatherEvent`."""

    return WeatherEvent(
        timestamp=raw["timestamp"],
        temperature=float(raw.get("temperature", 0.0)),
        humidity=float(raw.get("humidity", 0.0)),
        precipitation=float(raw.get("precipitation", 0.0)),
        wind=float(raw.get("wind", 0.0)),
        visibility=float(raw.get("visibility", 0.0)),
        pressure=float(raw.get("pressure", 0.0)),
        lightning=bool(raw.get("lightning", False)),
    )


def run_weather_etl(
    db: ConnectionProtocol, clients: Iterable[WeatherClient]
) -> list[WeatherEvent]:
    """Fetch data from ``clients`` and persist to ``db``.

    Returns the list of normalized :class:`WeatherEvent` objects that were
    inserted.  The database interaction is intentionally simple: each event
    results in a single ``INSERT`` command recorded on the connection.
    """

    events: list[WeatherEvent] = []
    for client in clients:
        event = normalize(client.fetch())
        db.execute_command(
            "INSERT INTO weather_events (timestamp, temperature, humidity, precipitation, wind, visibility, pressure, lightning)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                event.timestamp,
                event.temperature,
                event.humidity,
                event.precipitation,
                event.wind,
                event.visibility,
                event.pressure,
                event.lightning,
            ),
        )
        events.append(event)
    return events


# ---------------------------------------------------------------------------
# Event feed connectors
# ---------------------------------------------------------------------------


class EventConnector(Protocol):
    """Protocol representing a generic event feed."""

    def fetch(self) -> Sequence[dict]:
        ...


class SocialMediaConnector:
    """Connector for social media feeds.

    Parameters
    ----------
    fetch_fn:
        Callable returning an iterable of event dictionaries.  Each event must
        contain at least a ``timestamp`` field and may include additional
        metadata such as ``sentiment``.
    """

    def __init__(self, fetch_fn: Callable[[], Sequence[dict]]):
        self._fetch = fetch_fn

    def fetch(self) -> Sequence[dict]:  # pragma: no cover - thin wrapper
        return self._fetch()


class LocalEventConnector:
    """Connector for local event feeds."""

    def __init__(self, fetch_fn: Callable[[], Sequence[dict]]):
        self._fetch = fetch_fn

    def fetch(self) -> Sequence[dict]:  # pragma: no cover - thin wrapper
        return self._fetch()


def merge_environmental_data(
    weather_events: Iterable[WeatherEvent],
    event_records: Iterable[dict],
) -> pd.DataFrame:
    """Merge weather data with additional event records."""

    w_df = pd.DataFrame([e.__dict__ for e in weather_events])
    e_df = pd.DataFrame(list(event_records))
    if not e_df.empty:
        e_df = e_df.groupby("timestamp").sum(numeric_only=True).reset_index()
    return (
        pd.merge(w_df, e_df, on="timestamp", how="outer")
        .sort_values("timestamp")
        .fillna(0)
    )


# ---------------------------------------------------------------------------
# Correlation utilities
# ---------------------------------------------------------------------------

AccessRecord = Tuple[str, str]
TimedAccessRecord = Tuple[datetime, str, str]


def correlate_access_with_weather(
    access_records: Iterable[TimedAccessRecord],
    weather_events: Iterable[WeatherEvent],
    window: timedelta,
    spike_threshold: int,
) -> List[datetime]:
    """Flag weather events that coincide with access spikes."""

    times = sorted(ts for ts, _u, _r in access_records)
    flagged: List[datetime] = []
    for event in weather_events:
        start = event.timestamp - window
        end = event.timestamp + window
        count = 0
        for t in times:
            if t < start:
                continue
            if t > end:
                break
            count += 1
        if count >= spike_threshold:
            flagged.append(event.timestamp)
    return flagged


__all__ = [
    "WeatherEvent",
    "WeatherClient",
    "run_weather_etl",
    "normalize",
    "SocialMediaConnector",
    "LocalEventConnector",
    "merge_environmental_data",
    "correlate_access_with_weather",
    "AccessRecord",
    "TimedAccessRecord",
]
