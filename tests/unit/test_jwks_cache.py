import importlib
import io
import json
import logging
import socket
import types

import pytest


def setup_auth(monkeypatch):
    # stub jose.jwt before importing core.auth
    import jose.jwt as orig_jwt

    jwt_stub = types.SimpleNamespace(
        decode=lambda *a, **kw: {"decoded": True},
        get_unverified_header=lambda token: {"kid": "testkey"},
    )

    monkeypatch.setattr(orig_jwt, "decode", jwt_stub.decode)
    monkeypatch.setattr(
        orig_jwt, "get_unverified_header", jwt_stub.get_unverified_header
    )

    from yosai_intel_dashboard.src.infrastructure.config import reload_config

    reload_config()
    module = importlib.import_module("core.auth")
    importlib.reload(module)
    return module


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def test_jwks_cached(monkeypatch):
    auth = setup_auth(monkeypatch)
    jwks = {"keys": [{"kid": "testkey"}]}
    count = {"calls": 0}

    def fake_urlopen(url):
        count["calls"] += 1
        return FakeResp(json.dumps(jwks).encode())

    monkeypatch.setattr(auth, "urlopen", fake_urlopen)
    monkeypatch.setenv("JWKS_CACHE_TTL", "100")

    auth._jwks_cache.clear()
    auth._decode_jwt("t", "example.com", "aud", "cid")
    auth._decode_jwt("t", "example.com", "aud", "cid")
    assert count["calls"] == 1


def test_jwks_cache_expired(monkeypatch):
    auth = setup_auth(monkeypatch)
    jwks = {"keys": [{"kid": "testkey"}]}
    count = {"calls": 0}

    def fake_urlopen(url):
        count["calls"] += 1
        return FakeResp(json.dumps(jwks).encode())

    monkeypatch.setattr(auth, "urlopen", fake_urlopen)
    monkeypatch.setenv("JWKS_CACHE_TTL", "1")

    base_time = 1000
    current = {"t": base_time}

    def fake_time():
        return current["t"]

    monkeypatch.setattr(auth.time, "time", fake_time)

    auth._jwks_cache.clear()
    auth._decode_jwt("t", "example.com", "aud", "cid")
    assert count["calls"] == 1

    current["t"] = base_time + 2
    auth._decode_jwt("t", "example.com", "aud", "cid")
    assert count["calls"] == 2


def test_jwks_fetch_timeout(monkeypatch, caplog):
    auth = setup_auth(monkeypatch)

    def fake_urlopen(url, timeout=None):
        raise socket.timeout("timed out")

    monkeypatch.setattr(auth, "urlopen", fake_urlopen)
    auth._jwks_cache.clear()

    with caplog.at_level("WARNING"):
        with pytest.raises(socket.timeout):
            auth._get_jwks("example.com")

    assert any("Failed to fetch JWKS" in r.getMessage() for r in caplog.records)
