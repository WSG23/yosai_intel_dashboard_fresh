from shared.events.bus import EventBus
from shared.events.names import EventName


def test_callbacks_use_standard_event_names() -> None:
    bus = EventBus()
    metrics: list[dict] = []
    analytics: list[dict] = []

    bus.subscribe(EventName.METRICS_UPDATE, lambda payload: metrics.append(payload))
    bus.subscribe(EventName.ANALYTICS_UPDATE, lambda payload: analytics.append(payload))

    bus.publish(EventName.METRICS_UPDATE, {"a": 1})
    bus.publish(EventName.ANALYTICS_UPDATE, {"b": 2})

    assert metrics == [{"a": 1}]
    assert analytics == [{"b": 2}]
