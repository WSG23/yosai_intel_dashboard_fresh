from analytics_core.callbacks.unified_callback_manager import CallbackManager
from yosai_intel_dashboard.src.core.callback_events import CallbackEvent


def test_priority_and_async_trigger():
    manager = CallbackManager()
    events = []

    async def async_cb():
        events.append("async")

    def sync_cb():
        events.append("sync")

    manager.register_callback(CallbackEvent.BEFORE_REQUEST, sync_cb, priority=10)
    manager.register_callback(CallbackEvent.BEFORE_REQUEST, async_cb, priority=0)

    manager.trigger(CallbackEvent.BEFORE_REQUEST)
    assert events == ["async", "sync"]

    metrics = manager.get_metrics(CallbackEvent.BEFORE_REQUEST)
    assert metrics["calls"] == 2
