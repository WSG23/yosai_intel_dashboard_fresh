import httpx
import pytest

from shared.httpx import BreakerClient
from services.resilience.circuit_breaker import CircuitBreakerOpen


@pytest.mark.asyncio
async def test_breaker_client_uses_fallback(monkeypatch):
    client = BreakerClient()

    async def deny() -> bool:
        return False

    monkeypatch.setattr(client.circuit_breaker, "allows_request", deny)

    called = False

    async def fallback() -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, text="fallback")

    result = await client.request("GET", "http://example.com", fallback=fallback)
    assert called is True
    assert result.text == "fallback"


@pytest.mark.asyncio
async def test_breaker_client_raises_without_fallback(monkeypatch):
    client = BreakerClient()

    async def deny() -> bool:
        return False

    monkeypatch.setattr(client.circuit_breaker, "allows_request", deny)

    with pytest.raises(CircuitBreakerOpen):
        await client.request("GET", "http://example.com")
