import asyncio
import time
import types
import sys

import pytest

# Stub minimal core modules to avoid heavy imports during tests
core_stub = types.ModuleType("yosai_intel_dashboard.src.core")
core_stub.__path__ = []
base_model_stub = types.ModuleType("yosai_intel_dashboard.src.core.base_model")
base_model_stub.__path__ = []


class BaseModel:
    def __init__(self, config=None, db=None, logger=None):
        pass


base_model_stub.BaseModel = BaseModel
core_stub.base_model = base_model_stub
sys.modules["yosai_intel_dashboard.src.core"] = core_stub
sys.modules["yosai_intel_dashboard.src.core.base_model"] = base_model_stub

from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


class AsyncWarmService:
    def __init__(self):
        self.initialized = False

    async def initialize_async(self) -> None:  # pragma: no cover - executed in tests
        await asyncio.sleep(0.1)
        self.initialized = True


class SyncWarmService:
    def __init__(self):
        self.initialized = False

    def initialize(self) -> None:  # pragma: no cover - executed in executor
        time.sleep(0.1)
        self.initialized = True


def test_initialize_async_reduces_startup_time():
    container = ServiceContainer()
    container.register_singleton("a", AsyncWarmService, factory=lambda c: AsyncWarmService())
    container.register_singleton("b", AsyncWarmService, factory=lambda c: AsyncWarmService())

    # Measure sequential warm-up
    svc1, svc2 = AsyncWarmService(), AsyncWarmService()
    start_seq = time.perf_counter()
    asyncio.run(svc1.initialize_async())
    asyncio.run(svc2.initialize_async())
    sequential = time.perf_counter() - start_seq

    # Measure concurrent warm-up via container
    start_conc = time.perf_counter()
    asyncio.run(container.initialize_async())
    concurrent = time.perf_counter() - start_conc

    assert concurrent < sequential
    assert container.get("a").initialized
    assert container.get("b").initialized


def test_initialize_async_non_blocking():
    container = ServiceContainer()
    container.register_singleton("sync", SyncWarmService, factory=lambda c: SyncWarmService())

    async def runner():
        async def short_task():
            await asyncio.sleep(0.05)

        task = asyncio.create_task(short_task())
        start = time.perf_counter()
        await asyncio.gather(container.initialize_async(), task)
        duration = time.perf_counter() - start

        assert duration < 0.15  # would be ~0.15 if the event loop was blocked
        assert container.get("sync").initialized

    asyncio.run(runner())
