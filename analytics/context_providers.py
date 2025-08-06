"""Utilities for fetching environmental context from external APIs.

This module provides thin wrappers around optional third-party services
such as weather, local events and social media sentiment APIs.  The
functions are intentionally lightweight so unit tests can stub them out
without performing real network calls.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class ContextData:
    """Simple container for gathered context information."""

    weather: Dict[str, Any]
    events: List[Dict[str, Any]]
    social: Dict[str, Any]


def fetch_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """Fetch current weather information.

    Uses the `WEATHER_API_URL` environment variable if set, otherwise
    defaults to the free `open-meteo.com` endpoint.  The return structure
    is a dictionary containing at least ``temperature`` and ``windspeed``
    when available.  Any network or parsing errors are swallowed and an
    empty dictionary is returned; callers may decide how to handle
    incomplete information.
    """

    url = os.environ.get("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")
    params = {"latitude": latitude, "longitude": longitude, "current_weather": True}
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json().get("current_weather", {})
        return {
            "temperature": data.get("temperature"),
            "wind_speed": data.get("windspeed"),
            "condition": data.get("weathercode"),
        }
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Weather fetch failed: %s", exc)
        return {}


def fetch_local_events(city: str) -> List[Dict[str, Any]]:
    """Retrieve upcoming local events for *city*.

    The API endpoint can be configured via ``EVENTS_API_URL``.  For the
    sake of this repository the returned value is a list of dictionaries
    with ``name`` and ``start`` keys.  Similar to :func:`fetch_weather`,
    failures result in an empty list.
    """

    url = os.environ.get("EVENTS_API_URL")
    if not url:
        return []
    try:
        resp = requests.get(url, params={"city": city}, timeout=5)
        resp.raise_for_status()
        items = resp.json().get("events", [])
        return [
            {"name": item.get("name"), "start": item.get("start")} for item in items
        ]
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Event fetch failed: %s", exc)
        return []


def fetch_social_signals(topic: str) -> Dict[str, Any]:
    """Fetch basic social media sentiment for the given *topic*.

    A trivial JSON structure is returned: ``{"sentiment": float}`` where
    ``sentiment`` ranges from -1 (negative) to 1 (positive).  The API
    endpoint is configured via ``SOCIAL_API_URL``.
    """

    url = os.environ.get("SOCIAL_API_URL")
    if not url:
        return {}
    try:
        resp = requests.get(url, params={"q": topic}, timeout=5)
        resp.raise_for_status()
        return {"sentiment": resp.json().get("sentiment", 0)}
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Social signal fetch failed: %s", exc)
        return {}


def gather_context(
    *, latitude: float, longitude: float, city: str, topic: Optional[str] = None
) -> ContextData:
    """Gather context from all available providers.

    Parameters
    ----------
    latitude, longitude:
        Location information used for weather services.
    city:
        Used for event lookups.
    topic:
        Optional search term for social media sentiment analysis.  If not
        provided, the *city* name will be used.
    """

    weather = fetch_weather(latitude, longitude)
    events = fetch_local_events(city)
    social = fetch_social_signals(topic or city)
    return ContextData(weather=weather, events=events, social=social)
