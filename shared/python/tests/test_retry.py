import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))
from shared.python.retry import aretry, retry


def test_retry_eventual_success():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 2:
            raise ValueError("boom")
        return "ok"

    assert retry(fn, attempts=2, base_delay=0) == "ok"
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_aretry_eventual_success():
    calls = {"n": 0}

    async def fn():
        calls["n"] += 1
        if calls["n"] < 2:
            raise ValueError("boom")
        return "ok"

    assert await aretry(fn, attempts=2, base_delay=0) == "ok"
    assert calls["n"] == 2
