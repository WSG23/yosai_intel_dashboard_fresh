from __future__ import annotations

import os

import pytest

os.environ.setdefault("CACHE_TTL", "1")
os.environ.setdefault("CACHE_TTL_SECONDS", "1")
os.environ.setdefault("JWKS_CACHE_TTL", "1")

from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.core.exceptions import ValidationError


class DummyModel:
    def __init__(self, result: int) -> None:
        self.result = result

    def predict(self, _):  # pragma: no cover - trivial
        return [self.result]


@pytest.fixture
def normal_model():
    return DummyModel(1)


@pytest.fixture
def anomalous_model():
    return DummyModel(-1)


def test_anomaly_model_allows_normal_input(normal_model):
    validator = SecurityValidator(anomaly_model=normal_model)
    assert validator.validate_input("safe") == {"valid": True, "sanitized": "safe"}


def test_anomaly_model_rejects_outlier(anomalous_model):
    validator = SecurityValidator(anomaly_model=anomalous_model)
    with pytest.raises(ValidationError):
        validator.validate_input("bad")
