import importlib


def test_redis_asyncio_import() -> None:
    module = importlib.import_module("redis.asyncio")
    assert module is not None
