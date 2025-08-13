import pytest


@pytest.mark.asyncio
async def test_startup_fails_without_secret(app_factory):
    module, _, _ = app_factory(secret=None)
    with pytest.raises(RuntimeError):
        await module._startup()


@pytest.mark.asyncio
async def test_startup_succeeds_with_secret(app_factory):
    module, _, _ = app_factory(secret="super-secret")
    await module._startup()
    assert module._jwt_secret() == "super-secret"
