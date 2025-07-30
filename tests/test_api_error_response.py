import pytest
from flask import Flask

from error_handling import api_error_response, ErrorCategory


def test_api_error_response_generates_json_and_status():
    app = Flask(__name__)
    with app.app_context():
        resp, status = api_error_response(ValueError("bad"), ErrorCategory.INVALID_INPUT)
        assert status == 400
        assert resp.get_json() == {"code": "invalid_input", "message": "bad"}

