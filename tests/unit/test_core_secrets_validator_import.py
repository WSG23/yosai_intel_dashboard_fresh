import importlib


def test_validate_production_secrets_importable():
    module = importlib.import_module("core.secrets_validator")
    assert hasattr(module, "validate_production_secrets")
