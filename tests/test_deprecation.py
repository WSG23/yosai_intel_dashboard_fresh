import warnings

from yosai_intel_dashboard.src.core import performance
from yosai_intel_dashboard.src.core.deprecation import deprecated


class Dummy:
    @deprecated("1.0", removal="2.0", migration="use new_func()", track_usage=True)
    def old(self, x):
        return x * 2


def test_deprecated_warns_and_records(monkeypatch):
    monitor = performance.PerformanceMonitor(max_metrics=10)
    monkeypatch.setattr(performance, "_performance_monitor", monitor)

    dummy = Dummy()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        assert dummy.old(3) == 6

    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert any(m.name == "deprecated.old" for m in monitor.metrics)


def test_deprecated_no_tracking(monkeypatch):
    monitor = performance.PerformanceMonitor(max_metrics=10)
    monkeypatch.setattr(performance, "_performance_monitor", monitor)

    @deprecated("1.0", track_usage=False)
    def func():
        return "ok"

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        assert func() == "ok"

    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert not any(m.name == "deprecated.func" for m in monitor.metrics)
