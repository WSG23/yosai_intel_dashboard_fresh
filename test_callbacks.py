"""Tests for callback registration."""

import importlib

from core.app_factory import create_app


def test_upload_module_import() -> None:
    """Ensure the upload module exposes expected helpers."""

    mod = importlib.import_module("pages.file_upload")

    assert hasattr(mod, "layout")
    assert hasattr(mod, "register_callbacks")


def test_callback_registration(dash_duo) -> None:
    """Verify callbacks are registered and the upload page renders."""

    app = create_app()
    assert hasattr(app, "callback_map")
    assert app.callback_map

    upload_callbacks = [cid for cid in app.callback_map if "upload" in cid.lower()]
    assert upload_callbacks

    dash_duo.start_server(app)
    dash_duo.driver.get(dash_duo.server_url + "/upload")
    dash_duo.find_element("#upload-data")
