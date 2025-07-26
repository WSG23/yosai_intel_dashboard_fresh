import pytest

pytest.importorskip('yosai_intel_dashboard.src.core.entities.user')


def test_user_module_importable():
    module = __import__('yosai_intel_dashboard.src.core.entities.user', fromlist=[''])
    assert module is not None
