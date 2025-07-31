from yosai_intel_dashboard.src.services.analytics.events.subscriber import Subscriber


class DummyBus:
    def __init__(self):
        self.called = False

    def subscribe(self, event, handler):
        self.called = True


def test_subscribe():
    bus = DummyBus()
    sub = Subscriber(bus)
    sub.subscribe("evt", lambda x: x)
    assert bus.called
