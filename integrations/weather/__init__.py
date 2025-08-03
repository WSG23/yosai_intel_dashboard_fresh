"""Weather data integrations.

This package provides clients for external weather APIs and utilities to
normalize weather metrics for use by the analytics stack.
"""

from .clients import OpenWeatherMapClient, NOAAClient, LocalSensorClient
from .etl import WeatherEvent, run_weather_etl

__all__ = [
    "OpenWeatherMapClient",
    "NOAAClient",
    "LocalSensorClient",
    "WeatherEvent",
    "run_weather_etl",
]
