import importlib.util
import pathlib
import sys
import types

import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

services_path = pathlib.Path(__file__).resolve().parents[2] / "services"
stub_pkg = types.ModuleType("services")
stub_pkg.__path__ = [str(services_path)]
safe_import('services', stub_pkg)
stub_interfaces = types.ModuleType("services.interfaces")


class AnalyticsServiceProtocol:
    pass


stub_interfaces.AnalyticsServiceProtocol = AnalyticsServiceProtocol
safe_import('services.interfaces', stub_interfaces)
safe_import('kafka', types.ModuleType("kafka"))
setattr(sys.modules["kafka"], "KafkaProducer", object)

circuit_path = services_path / "resilience" / "circuit_breaker.py"
cb_spec = importlib.util.spec_from_file_location(
    "services.resilience.circuit_breaker",
    circuit_path,
)
circuit_breaker = importlib.util.module_from_spec(cb_spec)
cb_spec.loader.exec_module(circuit_breaker)  # type: ignore
CircuitBreaker = circuit_breaker.CircuitBreaker
CircuitBreakerOpen = circuit_breaker.CircuitBreakerOpen

# Load EventServiceAdapter with minimal dependencies
spec = importlib.util.spec_from_file_location(
    "migration_adapter",
    pathlib.Path(__file__).resolve().parents[2]
    / "services"
    / "migration"
    / "adapter.py",
)
migration_adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_adapter)  # type: ignore
EventServiceAdapter = migration_adapter.EventServiceAdapter


@pytest.mark.asyncio
async def test_circuit_breaker_state_transitions(monkeypatch):
    cb_mod = circuit_breaker

    t = 1000.0
    monkeypatch.setattr(cb_mod.time, "time", lambda: t)
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10, name="test")

    assert await cb.allows_request() is True
    await cb.record_failure()
    assert await cb.allows_request() is True
    await cb.record_failure()
    assert await cb.allows_request() is False

    t += 11
    assert await cb.allows_request() is True


@pytest.mark.asyncio
async def test_event_service_fallback_on_open(monkeypatch):
    adapter = EventServiceAdapter(base_url="http://localhost")
    adapter.kafka_producer = None

    async def always_false():
        return False

    monkeypatch.setattr(adapter.circuit_breaker, "allows_request", always_false)

    result = await adapter._process_event({"event_id": "E1"})
    assert result["status"] == "unavailable"
