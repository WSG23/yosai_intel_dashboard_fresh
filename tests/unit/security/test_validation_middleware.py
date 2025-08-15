import json

from flask import Flask

from yosai_intel_dashboard.src.infrastructure.security.validation_middleware import (
    ValidationMiddleware,
)


def _create_upload_app() -> Flask:
    app = Flask(__name__)
    middleware = ValidationMiddleware()
    app.before_request(middleware.validate_request)
    app.after_request(middleware.sanitize_response)

    @app.route("/_dash-update-component", methods=["POST"])
    def upload():
        return "ok"

    return app


def test_dash_update_large_body_allowed():
    app = _create_upload_app()
    client = app.test_client()
    payload = {"text": "<" + "a" * (2 * 1024 * 1024) + ">"}
    resp = client.post(
        "/_dash-update-component",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200
