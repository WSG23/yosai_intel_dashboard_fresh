import sys
import time
import types
from pathlib import Path
import asyncio
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
os.environ.setdefault("SECRET_KEY", "test")


class FakeRedis:
    def __init__(self):
        self.store = {}
        self.expire_at = {}

    async def incr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    async def expire(self, key: str, seconds: int) -> None:
        self.expire_at[key] = time.time() + seconds

    async def ttl(self, key: str) -> int:
        exp = self.expire_at.get(key)
        if exp is None:
            return -2
        remaining = int(exp - time.time())
        if remaining <= 0:
            self.store.pop(key, None)
            self.expire_at.pop(key, None)
            return -2
        return remaining

    async def set(self, key: str, value: int, ex: int | None = None) -> None:
        self.store[key] = value
        if ex is not None:
            self.expire_at[key] = time.time() + ex

    async def scan_iter(self, match: str | None = None):
        prefix = match[:-1] if match and match.endswith("*") else match
        for key in list(self.expire_at.keys()):
            if prefix is None or key.startswith(prefix):
                yield key

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)
        self.expire_at.pop(key, None)


# Stub out heavy SecurityValidator dependency before import
validator_stub = types.ModuleType("validation.security_validator")
validator_stub.SecurityValidator = object  # type: ignore[attr-defined]
sys.modules["validation.security_validator"] = validator_stub

core_registry_stub = types.ModuleType("yosai_intel_dashboard.src.core.registry")
core_registry_stub.ServiceRegistry = object  # type: ignore[attr-defined]
core_registry_stub.registry = object()
sys.modules["yosai_intel_dashboard.src.core.registry"] = core_registry_stub

access_events_stub = types.ModuleType(
    "yosai_intel_dashboard.src.core.domain.entities.access_events"
)
access_events_stub.AccessEventModel = object  # type: ignore[attr-defined]
sys.modules[
    "yosai_intel_dashboard.src.core.domain.entities.access_events"
] = access_events_stub

base_model_stub = types.ModuleType("yosai_intel_dashboard.src.core.base_model")
base_model_stub.BaseModel = object  # type: ignore[attr-defined]
sys.modules["yosai_intel_dashboard.src.core.base_model"] = base_model_stub

secret_manager_stub = types.ModuleType("yosai_intel_dashboard.src.core.secret_manager")
secret_manager_stub.SecretsManager = object  # type: ignore[attr-defined]
sys.modules["yosai_intel_dashboard.src.core.secret_manager"] = secret_manager_stub

dynamic_config_stub = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.config.dynamic_config"
)
dynamic_config_stub.dynamic_config = types.SimpleNamespace(
    security=types.SimpleNamespace(
        rate_limit_requests=5, rate_limit_window_minutes=1, pbkdf2_iterations=1000
    )
)
sys.modules[
    "yosai_intel_dashboard.src.infrastructure.config.dynamic_config"
] = dynamic_config_stub

anomaly_detector_stub = types.ModuleType(
    "yosai_intel_dashboard.src.infrastructure.monitoring.anomaly_detector"
)
anomaly_detector_stub.AnomalyDetector = object  # type: ignore[attr-defined]
sys.modules[
    "yosai_intel_dashboard.src.infrastructure.monitoring.anomaly_detector"
] = anomaly_detector_stub

argon2_stub = types.ModuleType("argon2")
argon2_stub.PasswordHasher = object  # type: ignore[attr-defined]
argon2_stub.exceptions = types.SimpleNamespace(VerifyMismatchError=Exception)
sys.modules["argon2"] = argon2_stub

pandas_stub = types.ModuleType("pandas")
pandas_stub.DataFrame = type("DataFrame", (), {})
sys.modules["pandas"] = pandas_stub

pydantic_stub = types.ModuleType("pydantic")
class _BaseModel:  # simple stand-in
    pass
pydantic_stub.BaseModel = _BaseModel
pydantic_stub.ValidationError = Exception
pydantic_stub.validator = lambda *a, **k: (lambda f: f)
sys.modules["pydantic"] = pydantic_stub

yaml_stub = types.ModuleType("yaml")
yaml_stub.safe_load = lambda *a, **k: {}
sys.modules["yaml"] = yaml_stub

dash_stub = types.ModuleType("dash")
dash_stub.Dash = object  # type: ignore[attr-defined]
sys.modules["dash"] = dash_stub

dash_dependencies_stub = types.ModuleType("dash.dependencies")
_Dep = type("_Dep", (), {})
dash_dependencies_stub.Input = _Dep
dash_dependencies_stub.Output = _Dep
dash_dependencies_stub.State = _Dep
sys.modules["dash.dependencies"] = dash_dependencies_stub

jsonschema_stub = types.ModuleType("jsonschema")
jsonschema_stub.validate = lambda *a, **k: None
sys.modules["jsonschema"] = jsonschema_stub

# Load RateLimiter from security module without executing global side effects
security_path = Path("yosai_intel_dashboard/src/core/security.py")
source = security_path.read_text()
source = source.split("rate_limiter = RateLimiter()")[0]
security_module = types.ModuleType("security_module")
sys.modules["security_module"] = security_module
exec(compile(source, str(security_path), "exec"), security_module.__dict__)
RateLimiter = security_module.RateLimiter
security_module.asyncio = asyncio
import contextlib
security_module.contextlib = contextlib


@pytest.mark.asyncio
async def test_ttl_expiration_allows_after_window(monkeypatch):
    redis_client = FakeRedis()
    limiter = RateLimiter(redis_client, max_requests=1, window_minutes=1)
    current = [0.0]
    monkeypatch.setattr(time, "time", lambda: current[0])

    assert (await limiter.is_allowed("user"))["allowed"] is True
    assert (await limiter.is_allowed("user"))["allowed"] is False

    current[0] += 61  # advance past the window
    assert await redis_client.ttl("rl:req:user") == -2

    assert (await limiter.is_allowed("user"))["allowed"] is True


@pytest.mark.asyncio
async def test_cleanup_removes_expired_blocked_ips(monkeypatch):
    redis_client = FakeRedis()
    limiter = RateLimiter(redis_client, max_requests=1, window_minutes=1)
    current = [0.0]
    real_sleep = asyncio.sleep

    monkeypatch.setattr(time, "time", lambda: current[0])

    async def fast_sleep(seconds: float) -> None:
        current[0] += seconds
        await real_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    await limiter.is_allowed("user", "1.2.3.4")
    assert (await limiter.is_allowed("user", "1.2.3.4"))["allowed"] is False
    assert await redis_client.ttl("rl:block:1.2.3.4") > 0

    limiter.start_cleanup()
    await asyncio.sleep(limiter.window_seconds * 3)
    await redis_client.ttl("rl:req:user")
    ttl_after = await redis_client.ttl("rl:block:1.2.3.4")
    await limiter.stop_cleanup()

    assert ttl_after == -2
    assert (await limiter.is_allowed("user", "1.2.3.4"))["allowed"] is True
