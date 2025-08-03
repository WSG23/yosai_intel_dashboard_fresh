from __future__ import annotations

import pytest

# Reuse stubbed auth application fixture
from tests.integration.test_auth_flow import auth_app as _auth_app

auth_app = _auth_app


@pytest.mark.integration
def test_login_and_protected_access(auth_app) -> None:
    """Login sets session and allows protected endpoint access."""

    client = auth_app.test_client()

    # Access to protected route should redirect to login before authentication
    resp = client.get("/protected")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

    # Begin login flow
    resp = client.get("/login")
    assert resp.status_code == 302

    # Simulate callback with token exchange
    resp = client.get("/callback?code=fake")
    assert resp.status_code == 302

    # Session data should be set
    with client.session_transaction() as sess:
        assert sess["user_id"] == "user123"
        assert sess["roles"] == ["admin"]

    # Protected endpoint accessible after login
    resp = client.get("/protected")
    assert resp.status_code == 200
    assert resp.data == b"ok"
