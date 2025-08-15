from __future__ import annotations

from __future__ import annotations

import importlib.util

import pytest
from flask import Flask, request, session

# Import module directly from file to avoid package side effects
spec = importlib.util.spec_from_file_location(
    "behavioral_biometrics",
    "yosai_intel_dashboard/src/services/security/behavioral_biometrics/__init__.py",
)
behavioral = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(behavioral)  # type: ignore[attr-defined]


def _make_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = "test-key"
    return app


def test_training_and_detection():
    app = _make_app()
    headers = {
        "X-Biometric-Consent": "true",
        "X-Keystroke-Metrics": "0.1,0.2,0.3",
        "X-Gait-Data": "0.1,0.1",
    }
    with app.test_request_context(headers=headers):
        session["user_id"] = "alice"
        # First call trains the models and should pass
        assert behavioral.verify_behavioral_biometrics(request)

    # Matching sample should also pass
    with app.test_request_context(headers=headers):
        session["user_id"] = "alice"
        assert behavioral.verify_behavioral_biometrics(request)

    # Anomalous data should be rejected
    bad_headers = {
        "X-Biometric-Consent": "true",
        "X-Keystroke-Metrics": "5,5,5",
        "X-Gait-Data": "5,5",
    }
    with app.test_request_context(headers=bad_headers):
        session["user_id"] = "alice"
        assert not behavioral.verify_behavioral_biometrics(request)


def test_no_consent_fallback():
    app = _make_app()
    headers = {"X-Keystroke-Metrics": "9,9,9"}
    with app.test_request_context(headers=headers):
        session["user_id"] = "bob"
        # Without consent the biometrics are ignored
        assert behavioral.verify_behavioral_biometrics(request)

    # Even with wildly different data it still falls back because no model exists
    headers2 = {"X-Keystroke-Metrics": "1,2,3"}
    with app.test_request_context(headers=headers2):
        session["user_id"] = "bob"
        assert behavioral.verify_behavioral_biometrics(request)


def test_retention_policy():
    app = _make_app()
    headers = {
        "X-Biometric-Consent": "true",
        "X-Keystroke-Metrics": "0.1,0.2,0.3",
    }
    with app.test_request_context(headers=headers):
        session["user_id"] = "carol"
        assert behavioral.verify_behavioral_biometrics(request)

    # Purge immediately and ensure the next request retrains instead of failing
    behavioral.purge_expired_models(0)
    with app.test_request_context(headers=headers):
        session["user_id"] = "carol"
        assert behavioral.verify_behavioral_biometrics(request)
