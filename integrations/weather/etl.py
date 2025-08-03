from __future__ import annotations

"""ETL utilities for weather events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol

from database.protocols import ConnectionProtocol


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
    def fetch(self) -> dict:  # pragma: no cover - protocol definition
        ...


def normalize(raw: dict) -> WeatherEvent:
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


def run_weather_etl(db: ConnectionProtocol, clients: Iterable[WeatherClient]) -> list[WeatherEvent]:
    """Fetch data from ``clients`` and persist to ``db``.

    Returns the list of normalized :class:`WeatherEvent` objects that were
    inserted.  The database interaction is intentionally simple: each event
    results in a single ``INSERT`` command recorded on the connection.
    """

    events: list[WeatherEvent] = []
    for client in clients:
        event = normalize(client.fetch())
        db.execute_command(
            "INSERT INTO weather_events (timestamp, temperature, humidity, precipitation, wind, visibility, pressure, lightning) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
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


__all__ = ["WeatherEvent", "run_weather_etl", "normalize"]
