"""Smoke tests for the API service."""


def test_main_callable():
    """Ensure the start_api.main function is callable."""
    from services.api import start_api

    assert callable(start_api.main)
