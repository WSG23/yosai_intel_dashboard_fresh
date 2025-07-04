from services.summary_reporting import SummaryReporter


class FakeDB:
    def __init__(self, healthy=True):
        self.healthy = healthy

    def health_check(self):
        return self.healthy


def test_health_check_basic():
    reporter = SummaryReporter(None)
    health = reporter.health_check()
    assert health["service"] == "healthy"
    assert health["database"] == "not_configured"
