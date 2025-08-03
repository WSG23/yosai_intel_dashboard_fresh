import hashlib
import importlib
import sys
import types

import pytest

# Ensure real requests package
sys.modules.pop("requests", None)
requests = importlib.import_module("requests")
sys.modules["requests"] = requests

from shared.http_client import create_pinned_session


class DummySock:
    def __init__(self, cert: bytes):
        self._cert = cert

    def getpeercert(self, binary_form=True):
        return self._cert


class DummyConn:
    def __init__(self, sock):
        self.sock = sock


class DummyRaw:
    def __init__(self, conn):
        self.connection = conn


def _call_hooks(session, raw):
    resp = types.SimpleNamespace(raw=raw)
    for hook in session.hooks["response"]:
        hook(resp)


def test_pinned_session_verifies_fingerprint():
    cert = b"certdata"
    fp = hashlib.sha256(cert).hexdigest()
    raw = DummyRaw(DummyConn(DummySock(cert)))
    session = create_pinned_session(fp)
    _call_hooks(session, raw)

    bad_session = create_pinned_session("00" * 32)
    with pytest.raises(requests.exceptions.SSLError):
        _call_hooks(bad_session, raw)
