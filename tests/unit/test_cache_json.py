import asyncio

from yosai_intel_dashboard.src.core.cache_manager import CacheConfig, InMemoryCacheManager

manager = InMemoryCacheManager(CacheConfig())


def test_json_serialization_roundtrip(tmp_path):
    obj = {"a": 1}
    asyncio.run(manager.set("k", obj))
    assert asyncio.run(manager.get("k")) == obj
