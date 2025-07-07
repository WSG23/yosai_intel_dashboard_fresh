import importlib
import sys

import pytest


def test_file_upload_requires_services(monkeypatch):
    monkeypatch.setitem(sys.modules, "services.upload", None)
    monkeypatch.setitem(sys.modules, "services.upload.unified_controller", None)
    monkeypatch.setitem(sys.modules, "services.upload.upload_queue_manager", None)
    sys.modules.pop("pages.file_upload", None)
    with pytest.raises(ImportError):
        importlib.import_module("pages.file_upload")
