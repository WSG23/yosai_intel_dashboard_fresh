import pytest
from flask import Flask, Response

from yosai_intel_dashboard.src.utils.assets_utils import ensure_icon_cache_headers


def _make_app():
    flask_app = Flask(__name__)

    class DummyDash:
        server = flask_app

    return flask_app, DummyDash()


def test_icon_cache_headers():
    flask_app, dummy = _make_app()

    @flask_app.route("/assets/navbar_icons/foo.png")
    def icon():
        return Response(b"data", content_type="image/png")

    ensure_icon_cache_headers(dummy)

    client = flask_app.test_client()
    res = client.get("/assets/navbar_icons/foo.png")
    assert res.headers.get("Cache-Control") == "public, max-age=3600"
    assert "ETag" in res.headers
