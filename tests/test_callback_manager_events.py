from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from shared.events.bus import EventBus
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks


def test_priority_and_async_trigger():
    bus = EventBus()

    class StubValidator:
        def validate_input(self, value: str, _field: str) -> dict[str, object]:
            return {"valid": True, "sanitized": value}

    manager = TrulyUnifiedCallbacks(event_bus=bus, security_validator=StubValidator())
    events = []

    async def async_cb():
        events.append("async")

    def sync_cb():
        events.append("sync")

    bus.subscribe(CallbackEvent.BEFORE_REQUEST, sync_cb, priority=10)
    bus.subscribe(CallbackEvent.BEFORE_REQUEST, async_cb, priority=0)

    manager.trigger(CallbackEvent.BEFORE_REQUEST)
    assert events == ["async", "sync"]

    metrics = bus.get_metrics(CallbackEvent.BEFORE_REQUEST)
    assert metrics["calls"] == 2
