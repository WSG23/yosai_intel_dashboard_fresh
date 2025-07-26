import pytest

pytest.importorskip('yosai_intel_dashboard.src.adapters.api.routes')

def test_routes_module_importable():
    module = __import__('yosai_intel_dashboard.src.adapters.api.routes', fromlist=[''])
    assert module is not None
