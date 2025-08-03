import importlib.util
import pathlib

import pytest


def load_app(jwt_secret: str):
    module_path = pathlib.Path(__file__).parent / "test_endpoints_async.py"
    spec = importlib.util.spec_from_file_location("test_endpoints_async", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_app(jwt_secret)


@pytest.mark.asyncio
async def test_startup_fails_on_placeholder():
    module, _, _ = load_app(
        jwt_secret="vault:secret/data/dev#JWT_SECRET"
    )
    with pytest.raises(RuntimeError):
        await module._startup()
