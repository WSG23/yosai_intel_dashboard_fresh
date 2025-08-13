"""Smoke tests for the services package."""


def test_package_import():
    """Import the services package and ensure it has documentation."""
    import yosai_intel_dashboard.src.services as services

    assert services.__doc__
