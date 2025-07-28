import pytest

pytest.importorskip('api.routes')

def test_routes_module_importable():
    module = __import__('api.routes', fromlist=[''])
    assert module is not None
