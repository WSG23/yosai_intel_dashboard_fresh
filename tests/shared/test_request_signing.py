from shared.request_signing import sign_request, verify_request, HEADER_SIGNATURE, HEADER_TIMESTAMP


def test_sign_and_verify_roundtrip(monkeypatch):
    secret = "s3cr3t"
    method = "POST"
    path = "/test"
    body = b"payload"

    headers = sign_request(secret, method, path, body)
    assert HEADER_SIGNATURE in headers and HEADER_TIMESTAMP in headers
    assert verify_request(secret, method, path, body, headers)


def test_verify_rejects_modified_body(monkeypatch):
    secret = "s3cr3t"
    method = "POST"
    path = "/test"
    body = b"payload"

    headers = sign_request(secret, method, path, body)
    assert not verify_request(secret, method, path, b"other", headers)
