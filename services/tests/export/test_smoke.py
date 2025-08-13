"""Smoke tests for the services.export package."""

import pytest


def test_export_service_import() -> None:
    """Ensure ExportService can be imported when matplotlib is available."""
    pytest.importorskip("matplotlib")
    from yosai_intel_dashboard.src.services.export import ExportService

    assert ExportService.__name__ == "ExportService"
