import pytest

from shared.python.retry import aretry


@pytest.mark.asyncio
async def test_aretry_eventual_success():
    attempts = {"count": 0}

    async def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise ValueError("boom")
        return "ok"

    result = await aretry(flaky, attempts=3, base_delay=0, exceptions=(ValueError,))
    assert result == "ok"
