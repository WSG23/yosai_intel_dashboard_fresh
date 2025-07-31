import importlib.util
import pathlib
import sys
import types
import logging
import pytest

# Setup minimal environment to load EventServiceAdapter
services_path = pathlib.Path(__file__).resolve().parents[1] / "yosai_intel_dashboard" / "src" / "services"

core_pkg = types.ModuleType("core")
core_pkg.__path__ = []
service_container_mod = types.ModuleType("core.service_container")
class ServiceContainer: pass
service_container_mod.ServiceContainer = ServiceContainer
sys.modules.setdefault("core", core_pkg)
sys.modules.setdefault("core.service_container", service_container_mod)

stub_services = types.ModuleType("services")
stub_services.__path__ = [str(services_path)]
sys.modules.setdefault("services", stub_services)

interfaces_mod = types.ModuleType("services.interfaces")
class AnalyticsServiceProtocol: pass
interfaces_mod.AnalyticsServiceProtocol = AnalyticsServiceProtocol
sys.modules.setdefault("services.interfaces", interfaces_mod)

feat_mod = types.ModuleType("services.feature_flags")
class FeatureFlags:
    def __init__(self):
        self._flags = {}
    def is_enabled(self, name):
        return self._flags.get(name, False)
feat_mod.feature_flags = FeatureFlags()
stub_services.feature_flags = feat_mod
sys.modules.setdefault("services.feature_flags", feat_mod)

cb_mod = types.ModuleType("services.resilience.circuit_breaker")
class CircuitBreakerOpen(Exception):
    pass
class DummyBreaker:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
cb_mod.CircuitBreaker = DummyBreaker
cb_mod.CircuitBreakerOpen = CircuitBreakerOpen
sys.modules.setdefault("services.resilience.circuit_breaker", cb_mod)

sys.modules.setdefault("kafka", types.ModuleType("kafka"))
setattr(sys.modules["kafka"], "KafkaProducer", object)

spec = importlib.util.spec_from_file_location(
    "migration_adapter",
    services_path / "migration" / "adapter.py",
)
migration_adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_adapter)
EventServiceAdapter = migration_adapter.EventServiceAdapter

@pytest.mark.asyncio
async def test_init_logs(monkeypatch, caplog):
    def fail(*a, **k):
        raise RuntimeError("fail")
    monkeypatch.setattr(migration_adapter, "KafkaProducer", fail)
    with caplog.at_level(logging.WARNING):
        EventServiceAdapter(base_url="http://localhost")
    assert any("Kafka initialization failed" in r.getMessage() for r in caplog.records)

@pytest.mark.asyncio
async def test_kafka_send_failure_logs(monkeypatch, caplog):
    class FailingProducer:
        def send(self, *a, **k):
            class F:
                def get(self, timeout=None):
                    raise RuntimeError("boom")
            return F()
    monkeypatch.setattr(migration_adapter, "KafkaProducer", lambda *a, **k: FailingProducer())
    adapter = EventServiceAdapter(base_url="http://localhost")
    adapter.circuit_breaker = DummyBreaker()

    class DummyResp:
        async def json(self):
            return {"ok": True}
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass

    class DummySession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        def post(self, *a, **k):
            return DummyResp()

    monkeypatch.setattr(migration_adapter.aiohttp, "ClientSession", lambda *a, **k: DummySession())
    monkeypatch.setattr(migration_adapter.aiohttp, "ClientTimeout", lambda *a, **k: None)

    with caplog.at_level(logging.WARNING):
        await adapter._process_event({"event_id": "E1"})
    assert any("Kafka send failed" in r.getMessage() for r in caplog.records)
