import types
from flask import Flask, Blueprint

from core.error_handlers import register_error_handlers
from core.exceptions import ValidationError, ServiceUnavailableError


def _create_app():
    app = Flask(__name__)
    register_error_handlers(app)

    bp = Blueprint('fail', __name__)

    @bp.route('/fail')
    def fail_route():
        raise ValidationError('field', 'bad', 'invalid')

    @bp.route('/unavail')
    def unavail_route():
        raise ServiceUnavailableError('maintenance')

    @bp.route('/internal')
    def internal_route():
        raise RuntimeError('boom')

    app.register_blueprint(bp)
    return app


def test_yosai_base_exception_handled():
    app = _create_app()
    client = app.test_client()

    resp = client.get('/fail')
    assert resp.status_code == 400
    body = resp.get_json()
    assert body == {"code": "invalid", "message": "bad", "field": "field"}


def test_service_unavailable_error():
    app = _create_app()
    client = app.test_client()

    resp = client.get('/unavail')
    assert resp.status_code == 503
    assert resp.get_json() == {"code": "unavailable", "message": "maintenance"}


def test_generic_exception_handled():
    app = _create_app()
    client = app.test_client()

    resp = client.get('/internal')
    assert resp.status_code == 500
    body = resp.get_json()
    assert body["code"] == "internal"
    assert body["message"] == "boom"
