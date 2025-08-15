import pytest

pytest.importorskip("core.entities.user")


def test_user_module_importable():
    module = __import__("core.entities.user", fromlist=[""])
    assert module is not None
