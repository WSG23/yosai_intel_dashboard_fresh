import importlib
import json
import io
import sys
import types

import pytest


def setup_auth(monkeypatch):
    # stub jose.jwt before importing core.auth
    jwt_stub = types.SimpleNamespace(
        decode=lambda *a, **kw: {"decoded": True},
        get_unverified_header=lambda token: {"kid": "testkey"},
    )
    jose_stub = types.SimpleNamespace(jwt=jwt_stub)
    monkeypatch.setitem(sys.modules, "jose", jose_stub)
    monkeypatch.setitem(sys.modules, "jose.jwt", jwt_stub)

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

