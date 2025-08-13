"""Tests for the healthcheck utilities."""

import pytest

from yosai_intel_dashboard.src.services.common.healthcheck import (
    aggregate,
    check_with_timeout,
)


async def ok_probe():
    """A probe that succeeds."""
    return None


async def failing_probe():
    """A probe that raises an error."""
    raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_check_with_timeout_ok():
    result = await check_with_timeout("ok", ok_probe)
    assert result == {"ok": "ok"}


@pytest.mark.asyncio
async def test_check_with_timeout_failure():
    result = await check_with_timeout("bad", failing_probe)
    assert result == {"bad": "fail:RuntimeError"}


@pytest.mark.asyncio
async def test_aggregate_status():
    status = await aggregate([("ok", ok_probe), ("bad", failing_probe)])
    assert status == {
        "status": "fail",
        "checks": {"ok": "ok", "bad": "fail:RuntimeError"},
    }
