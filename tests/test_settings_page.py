import dash_bootstrap_components as dbc
from pages import settings
from config.dynamic_config import dynamic_config


def test_apply_system_config_updates_dynamic_config():
    alert = settings.apply_system_config(120, 10, 5000)
    assert dynamic_config.security.rate_limit_requests == 120
    assert dynamic_config.database.connection_timeout_seconds == 10
    assert dynamic_config.analytics.batch_size == 5000
    assert isinstance(alert, dbc.Alert)


def test_update_theme_returns_sanitized():
    sanitized = settings.register_callbacks.__globals__["sanitize_theme"]("LIGHT")
    assert sanitized == "light"

