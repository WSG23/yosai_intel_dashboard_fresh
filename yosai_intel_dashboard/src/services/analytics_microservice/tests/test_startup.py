import importlib.util
import pathlib
import sys
import types

import pytest


def load_app(jwt_secret: str):
    if "scipy" not in sys.modules:
        scipy_stub = types.ModuleType("scipy")
        scipy_stub.stats = types.ModuleType("scipy.stats")
        sys.modules["scipy"] = scipy_stub
        sys.modules["scipy.stats"] = scipy_stub.stats

    module_path = pathlib.Path(__file__).parent / "test_endpoints_async.py"
    spec = importlib.util.spec_from_file_location("test_endpoints_async", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["test_endpoints_async"] = module
    spec.loader.exec_module(module)
    return module.load_app(jwt_secret)


@pytest.mark.asyncio
async def test_startup_fails_on_placeholder():
    module, _, _ = load_app(jwt_secret="change-me")
    with pytest.raises(RuntimeError):
        await module._startup()
