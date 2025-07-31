import threading

from core.callback_events import CallbackEvent
from core.callbacks import TrulyUnifiedCallbacks as CallbackManager


def test_thread_safe_registration_and_trigger():
    manager = CallbackManager()
    event = CallbackEvent.ANALYSIS_START
    results = []

    def register(i: int) -> None:
        manager.register_callback(event, lambda *_: results.append(i))

    threads = [threading.Thread(target=register, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(manager.get_callbacks(event)) == 10
    manager.trigger(event, None)
    assert sorted(results) == list(range(10))


def test_error_isolation_and_metrics():
    manager = CallbackManager()
    event = CallbackEvent.SYSTEM_ERROR
    order = []

    def first(*_):
        order.append("first")

    def failing(*_):
        order.append("fail")
        raise RuntimeError("boom")

    manager.register_callback(event, first)
    manager.register_callback(event, failing)

    manager.trigger(event, None)
    metrics = manager.get_metrics(event)
    assert order == ["first", "fail"]
    assert metrics["calls"] == 2
    assert metrics["exceptions"] == 1
