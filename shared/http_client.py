from __future__ import annotations

import hashlib

import importlib
import requests

if not hasattr(requests, "Session"):
    requests = importlib.import_module("requests")


def create_pinned_session(
    fingerprint: str,
    cert: str | None = None,
    key: str | None = None,
    ca: str | None = None,
) -> requests.Session:
    fp = fingerprint.lower().replace(":", "")
    session = requests.Session()
    if cert and key:
        session.cert = (cert, key)
    if ca:
        session.verify = ca

    def _check_cert(response, *args, **kwargs):
        cert_bin = response.raw.connection.sock.getpeercert(binary_form=True)
        actual = hashlib.sha256(cert_bin).hexdigest()
        if actual.lower() != fp:
            raise requests.exceptions.SSLError("certificate fingerprint mismatch")
        return response

    session.hooks.setdefault("response", []).append(_check_cert)
    return session
