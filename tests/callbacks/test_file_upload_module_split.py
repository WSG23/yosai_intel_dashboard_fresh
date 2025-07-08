import importlib

from pages import file_upload


def test_module_imports():
    assert hasattr(file_upload, "layout")
    importlib.reload(file_upload)
    assert hasattr(file_upload, "register_upload_callbacks")

