from types import SimpleNamespace

import pytest

from tests.import_helpers import (
    safe_import,
    import_optional,
    HTTPClientDouble,
    CacheBackendDouble,
)


def test_safe_import_returns_stub_when_missing():
    stub = SimpleNamespace(value=42)
    result = safe_import("nonexistent_mod", lambda: stub)
    assert result is stub


def test_safe_import_raises_without_factory():
    with pytest.raises(ModuleNotFoundError):
        safe_import("another_missing_mod")


def test_import_optional_returns_default_stub():
    default = SimpleNamespace(x="y")
    result = import_optional("yet_missing_mod", default)
    assert result is default


def test_http_client_double_records_calls():
    client = HTTPClientDouble()
    client.get("/path", return_value="ok")
    client.post("/submit", data={"a": 1})
    assert client.requests[0][0] == "GET"
    assert client.requests[0][1] == "/path"
    assert client.requests[1][0] == "POST"
    assert client.requests[1][2]["data"] == {"a": 1}


def test_cache_backend_double_behaves_like_cache():
    cache = CacheBackendDouble()
    cache.set("k", "v")
    assert cache.get("k") == "v"
    cache.delete("k")
    assert cache.get("k") is None
