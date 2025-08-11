"""Smoke tests for the services package."""


def test_package_import():
    """Import the services package and ensure it has documentation."""
    import services

    assert services.__doc__
