from __future__ import annotations

"""Weather API clients.

The clients defined in this module provide minimal wrappers around the
OpenWeatherMap and NOAA public APIs.  They are intentionally lightweight so
that unit tests can easily stub out network access by injecting a custom
``http_get`` callable.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional, Protocol
import json
from urllib import request


class HttpGet(Protocol):
    """Callable signature for performing HTTP GET requests."""

    def __call__(self, url: str) -> bytes:  # pragma: no cover - protocol
        ...


def _default_http_get(url: str) -> bytes:
    with request.urlopen(url) as resp:  # pragma: no cover - network
        return resp.read()


@dataclass
class OpenWeatherMapClient:
    """Client for the OpenWeatherMap current weather endpoint."""

    api_key: str
    lat: float
    lon: float
    http_get: HttpGet = _default_http_get

    def fetch(self) -> dict:
        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={self.lat}&lon={self.lon}&appid={self.api_key}&units=metric"
        )
        payload = json.loads(self.http_get(url).decode("utf-8"))
        return {
            "timestamp": datetime.fromtimestamp(payload["dt"], tz=timezone.utc),
            "temperature": payload["main"]["temp"],
            "humidity": payload["main"]["humidity"],
            "precipitation": payload.get("rain", {}).get("1h", 0.0),
            "wind": payload.get("wind", {}).get("speed", 0.0),
            "visibility": payload.get("visibility", 0.0),
            "pressure": payload["main"].get("pressure", 0.0),
            "lightning": any(w.get("id", 0) // 100 == 2 for w in payload.get("weather", [])),
        }


@dataclass
class NOAAClient:
    """Client for the NOAA latest observation endpoint."""

    station: str
    http_get: HttpGet = _default_http_get

    def fetch(self) -> dict:
        url = f"https://api.weather.gov/stations/{self.station}/observations/latest"
        payload = json.loads(self.http_get(url).decode("utf-8"))
        props = payload["properties"]
        return {
            "timestamp": datetime.fromisoformat(
                props["timestamp"].replace("Z", "+00:00")
            ),
            "temperature": props.get("temperature", {}).get("value"),
            "humidity": props.get("relativeHumidity", {}).get("value"),
            "precipitation": props.get("precipitationLastHour", {}).get("value", 0.0),
            "wind": props.get("windSpeed", {}).get("value"),
            "visibility": props.get("visibility", {}).get("value"),
            "pressure": props.get("barometricPressure", {}).get("value"),
            "lightning": False,  # NOAA endpoint does not report lightning directly
        }


class LocalSensorClient:
    """Simple client that reads metrics from a local sensor callback."""

    def __init__(self, reader: Callable[[], dict]) -> None:
        self._reader = reader

    def fetch(self) -> dict:
        data = self._reader()
        data.setdefault("timestamp", datetime.now(timezone.utc))
        return data


__all__ = ["OpenWeatherMapClient", "NOAAClient", "LocalSensorClient"]
