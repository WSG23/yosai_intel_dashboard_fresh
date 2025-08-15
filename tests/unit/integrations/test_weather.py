from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from integrations.weather.clients import (
    LocalSensorClient,
    NOAAClient,
    OpenWeatherMapClient,
)
from yosai_intel_dashboard.src.database.mock_database import MockDatabase
from yosai_intel_dashboard.src.services.environment import (
    LocalEventConnector,
    SocialMediaConnector,
    WeatherEvent,
    correlate_access_with_weather,
    merge_environmental_data,
    run_weather_etl,
)


def test_openweathermap_client_parses_metrics():
    sample = {
        "dt": 0,
        "main": {"temp": 20, "humidity": 80, "pressure": 1000},
        "wind": {"speed": 5},
        "visibility": 10000,
        "weather": [{"id": 200}],
        "rain": {"1h": 1.5},
    }

    def fake_get(url: str) -> bytes:
        return json.dumps(sample).encode("utf-8")

    client = OpenWeatherMapClient("k", 0.0, 0.0, http_get=fake_get)
    data = client.fetch()
    assert data["temperature"] == 20
    assert data["lightning"] is True
    assert data["precipitation"] == 1.5


def test_noaa_client_parses_metrics():
    sample = {
        "properties": {
            "timestamp": "2023-01-01T00:00:00+00:00",
            "temperature": {"value": 10},
            "relativeHumidity": {"value": 50},
            "precipitationLastHour": {"value": 0.2},
            "windSpeed": {"value": 3},
            "visibility": {"value": 5000},
            "barometricPressure": {"value": 90000},
        }
    }

    def fake_get(url: str) -> bytes:
        return json.dumps(sample).encode("utf-8")

    client = NOAAClient("STATION", http_get=fake_get)
    data = client.fetch()
    assert data["humidity"] == 50
    assert data["wind"] == 3


def test_local_sensor_client_returns_data():
    payload = {
        "timestamp": datetime.now(timezone.utc),
        "temperature": 5,
    }
    client = LocalSensorClient(lambda: payload)
    data = client.fetch()
    assert data["temperature"] == 5


def test_weather_etl_inserts_into_database():
    db = MockDatabase()
    now = datetime.now(timezone.utc)
    client = LocalSensorClient(
        lambda: {
            "timestamp": now,
            "temperature": 1,
            "humidity": 2,
            "precipitation": 3,
            "wind": 4,
            "visibility": 5,
            "pressure": 6,
            "lightning": True,
        }
    )
    events = run_weather_etl(db, [client])
    assert len(events) == 1
    assert db.commands  # insertion recorded


def test_correlate_access_with_weather_flags_spikes():
    t = datetime(2023, 1, 1, tzinfo=timezone.utc)
    weather = [
        WeatherEvent(
            timestamp=t,
            temperature=0,
            humidity=0,
            precipitation=10,
            wind=0,
            visibility=0,
            pressure=0,
            lightning=False,
        )
    ]
    access_records = [
        (t - timedelta(minutes=1), "u", "r"),
        (t - timedelta(minutes=2), "u", "r"),
        (t - timedelta(minutes=3), "u", "r"),
        (t - timedelta(minutes=4), "u", "r"),
        (t - timedelta(minutes=5), "u", "r"),
        (t - timedelta(minutes=6), "u", "r"),
    ]
    flagged = correlate_access_with_weather(
        access_records, weather, window=timedelta(minutes=5), spike_threshold=5
    )
    assert flagged == [t]


def test_merge_environmental_data_combines_sources():
    t = datetime.now(timezone.utc)
    weather = [
        WeatherEvent(
            timestamp=t,
            temperature=1,
            humidity=2,
            precipitation=0,
            wind=0,
            visibility=0,
            pressure=0,
            lightning=False,
        )
    ]
    social = SocialMediaConnector(lambda: [{"timestamp": t, "sentiment": 0.5}])
    local = LocalEventConnector(lambda: [{"timestamp": t, "events": 2}])
    events = list(social.fetch()) + list(local.fetch())
    merged = merge_environmental_data(weather, events)
    assert "sentiment" in merged and "events" in merged
    assert merged.iloc[0]["sentiment"] == 0.5
    assert merged.iloc[0]["events"] == 2
