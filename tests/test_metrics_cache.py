import time

from src.repository import CachedMetricsRepository, MetricsRepository


class DummyRepo(MetricsRepository):
    def __init__(self) -> None:
        self.calls = 0

    def get_performance_metrics(self):  # type: ignore[override]
        self.calls += 1
        return {"calls": self.calls}

    def get_drift_data(self):  # type: ignore[override]
        return {}

    def get_feature_importances(self):  # type: ignore[override]
        return {}


def test_cache_returns_cached_value_and_expires():
    repo = DummyRepo()
    cached = CachedMetricsRepository(repo, ttl=0.01)

    first = cached.get_performance_metrics()
    second = cached.get_performance_metrics()
    assert first == second
    assert repo.calls == 1

    time.sleep(0.02)
    third = cached.get_performance_metrics()
    assert third != first
    assert repo.calls == 2
