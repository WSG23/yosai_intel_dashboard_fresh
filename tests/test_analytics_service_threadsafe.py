from concurrent.futures import ThreadPoolExecutor

from yosai_intel_dashboard.src.services import analytics_service


def test_get_analytics_service_threadsafe(monkeypatch):
    # Reset global instance before test
    analytics_service._analytics_service = None

    def worker(_: int):
        return analytics_service.get_analytics_service()

    with ThreadPoolExecutor(max_workers=5) as exc:
        results = list(exc.map(worker, range(10)))

    first = results[0]
    for result in results:
        assert result is first
