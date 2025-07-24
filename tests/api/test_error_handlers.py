import types

from flask import Blueprint, Flask

from core.error_handlers import register_error_handlers
from core.exceptions import ValidationError


def _create_app():
    app = Flask(__name__)
    register_error_handlers(app)

    bp = Blueprint('fail', __name__)

    @bp.route('/fail')
    def fail_route():
        raise ValidationError('bad')

    app.register_blueprint(bp)
    return app


def test_yosai_base_exception_handled():
    app = _create_app()
    client = app.test_client()

    resp = client.get('/fail')
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code"] == "invalid_input"
    assert body["message"] == "bad"
