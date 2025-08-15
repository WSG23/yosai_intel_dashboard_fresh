from shared.events.names import EventName
from yosai_intel_dashboard.src.services.helpers.event_publisher import EventPublisher


class DummyPublisher:
    def __init__(self):
        self.called_with = None

    def publish(self, payload, event):
        self.called_with = (payload, event)


def test_event_publisher_delegates():
    dummy = DummyPublisher()
    publisher = EventPublisher(dummy)
    payload = {"foo": "bar"}
    publisher.publish(payload)
    assert dummy.called_with == (payload, EventName.ANALYTICS_UPDATE)

