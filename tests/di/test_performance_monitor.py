import time

from core.performance_monitor import DIPerformanceMonitor
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


def test_container_records_resolution_time():
    container = ServiceContainer()
    monitor = DIPerformanceMonitor()

    def factory(_c):
        time.sleep(0.01)
        return object()

    container.register_transient("svc", factory)

    original_get = container.get

    def monitored(service_key, proto=None):
        start = time.time()
        try:
            result = original_get(service_key, proto)
            monitor.record_service_resolution(service_key, time.time() - start)
            return result
        except Exception as exc:
            monitor.record_service_error(service_key, str(exc))
            raise

    container.get = monitored  # type: ignore

    container.get("svc")
    metrics = monitor.get_metrics_summary()["svc"]
    assert metrics["total_resolutions"] == 1
    assert metrics["average_time"] > 0
