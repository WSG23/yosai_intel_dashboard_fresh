from yosai_intel_dashboard.src.services.analytics.storage.repository import AnalyticsRepository


class DummyHelper:
    def get_analytics(self):
        return {"a": 1}


def test_repository():
    repo = AnalyticsRepository(DummyHelper())
    assert repo.get_analytics() == {"a": 1}
