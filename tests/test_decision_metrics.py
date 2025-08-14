import types

from monitoring import decision_metrics as dm


class DummyMetric:
    def __init__(self):
        self.count = 0
        self.last = None

    def labels(self, *a, **k):
        return self

    def inc(self):
        self.count += 1

    def observe(self, value):
        self.last = value


def test_record_decision_updates_metrics(monkeypatch):
    counter = DummyMetric()
    hist = DummyMetric()
    monkeypatch.setattr(dm, "decision_count", counter)
    monkeypatch.setattr(dm, "decision_latency", hist)
    dm.record_decision("svc", "allow", 0.1)
    assert counter.count == 1
    assert hist.last == 0.1


def test_track_decision_latency_context_manager(monkeypatch):
    counter = DummyMetric()
    hist = DummyMetric()
    monkeypatch.setattr(dm, "decision_count", counter)
    monkeypatch.setattr(dm, "decision_latency", hist)
    with dm.track_decision_latency("svc", "deny"):
        pass
    assert counter.count == 1
    assert hist.last is not None
