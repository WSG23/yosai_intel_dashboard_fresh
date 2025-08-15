import asyncio
import pytest

from yosai_intel_dashboard.src.error_handling.decorators import (
    DatabaseError,
    handle_errors,
)


@pytest.fixture
def async_runner():
    return asyncio.run


def test_sync_database_error_propagation():
    @handle_errors(reraise=True)
    def fail():
        raise DatabaseError("boom")

    with pytest.raises(DatabaseError):
        fail()


def test_async_database_error_propagation(async_runner):
    @handle_errors(reraise=True)
    async def fail_async():
        raise DatabaseError("boom")

    with pytest.raises(DatabaseError):
        async_runner(fail_async())
