import os

from shared.request_signing import (
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    sign_request,
    verify_request,
)


def _set_secret(monkeypatch) -> str:
    secret = os.urandom(16).hex()
    monkeypatch.setenv("REQUEST_SIGNING_SECRET", secret)
    return secret


def test_sign_and_verify_roundtrip(monkeypatch):
    secret = _set_secret(monkeypatch)
    method = "POST"
    path = "/test"
    body = b"payload"

    headers = sign_request(os.environ["REQUEST_SIGNING_SECRET"], method, path, body)
    assert HEADER_SIGNATURE in headers and HEADER_TIMESTAMP in headers
    # Ensure the secret is not leaked in headers
    assert secret not in headers.values()
    assert verify_request(os.environ["REQUEST_SIGNING_SECRET"], method, path, body, headers)


def test_verify_rejects_modified_body(monkeypatch):
    _set_secret(monkeypatch)
    method = "POST"
    path = "/test"
    body = b"payload"

    headers = sign_request(os.environ["REQUEST_SIGNING_SECRET"], method, path, body)
    assert not verify_request(
        os.environ["REQUEST_SIGNING_SECRET"], method, path, b"other", headers
    )
