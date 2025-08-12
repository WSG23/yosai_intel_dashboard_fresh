from shared.events import publish_event


class DummyBus:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def emit(self, event_type: str, data, source=None):
        self.events.append((event_type, data))


class FailingBus(DummyBus):
    def emit(self, event_type: str, data, source=None):
        raise RuntimeError("boom")


def test_publish_event_success():
    bus = DummyBus()
    publish_event(bus, {"a": 1}, event="evt")
    assert bus.events == [("evt", {"a": 1})]


def test_publish_event_no_bus():
    # should not raise
    publish_event(None, {"a": 1})


def test_publish_event_handles_error(caplog):
    bus = FailingBus()
    import logging

    caplog.set_level(logging.DEBUG)
    publish_event(bus, {"a": 1})
    assert not bus.events
    assert any("Event bus publish failed" in rec.message for rec in caplog.records)
