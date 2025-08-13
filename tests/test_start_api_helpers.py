import asyncio
import types

from start_api import _warm_cache, _ensure_health_endpoint


class DummyWarmer:
    last_instance = None

    def __init__(self, cache_manager, load_fn):
        type(self).last_instance = self
        self.cache_manager = cache_manager
        self.load_fn = load_fn
        self.path = None

    async def warm_from_file(self, path: str) -> None:  # pragma: no cover - simple stub
        self.path = path


class DummyCacheManager:
    def __init__(self) -> None:
        self.warm_args = None

    async def warm(self, keys, loader):
        self.warm_args = (keys, loader)

    def get(self, key):  # pragma: no cover - unused lookup
        return None


def test_warm_cache_executes(tmp_path):
    cache_manager = DummyCacheManager()
    cache_cfg = types.SimpleNamespace(usage_stats_path="usage.txt", warm_keys=["k1"])

    def load_fn(key):
        return None

    _warm_cache(cache_manager, cache_cfg, DummyWarmer, load_fn)
    assert cache_manager.warm_args == (["k1"], load_fn)
    assert DummyWarmer.last_instance.path == "usage.txt"


def test_ensure_health_endpoint_adds_route():
    class Route:
        def __init__(self, path):
            self.path = path

    class App:
        def __init__(self):
            self.routes = [Route("/other")]
            self.handler = None

        def get(self, path):
            def decorator(func):
                self.routes.append(Route(path))
                self.handler = func
                return func

            return decorator

    app = App()
    _ensure_health_endpoint(app)
    assert any(r.path == "/health" for r in app.routes)
    assert asyncio.run(app.handler()) == {"status": "ok"}
