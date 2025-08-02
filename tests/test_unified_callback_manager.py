import asyncio
import time

import pytest
from dash import Dash

from yosai_intel_dashboard.src.core import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.core.error_handling import error_handler

pytestmark = pytest.mark.usefixtures("fake_dash")


def test_execute_group_with_errors_and_retry():
    manager = TrulyUnifiedCallbacks(Dash(__name__))

    calls = {"fail": 0}

    def op_success(x):
        return x * 2

    def op_fail(x):
        calls["fail"] += 1
        if calls["fail"] < 2:
            raise ValueError("boom")
        return x + 1

    manager.register_operation("grp", op_success, name="s")
    manager.register_operation("grp", op_fail, name="f", retries=2)

    results = manager.execute_group("grp", 3)
    assert results == [6, 4]


def test_timeout_records_error():
    manager = TrulyUnifiedCallbacks(Dash(__name__))

    def slow():
        import time

        time.sleep(0.05)
        return True

    manager.register_operation("grp", slow, name="slow", timeout=0.01)
    res = manager.execute_group("grp")
    assert res == [None]
    assert any(
        ctx.message.startswith("Operation slow") for ctx in error_handler.error_history
    )


def test_execute_group_async(async_runner):
    manager = TrulyUnifiedCallbacks(Dash(__name__))

    async def slow(x):
        await asyncio.sleep(0.01)
        return x

    manager.register_operation("grp", slow, name="a")
    manager.register_operation("grp", slow, name="b")

    start = time.perf_counter()
    results = async_runner(manager.execute_group_async("grp", 7))
    duration = time.perf_counter() - start

    assert results == [7, 7]
    assert duration < 0.02
