import pytest

from shared.python.config_loader import ConfigError, get_bool, get_int, get_str


def test_get_str_required_missing(monkeypatch):
    with pytest.raises(ConfigError):
        get_str("MISSING_VAR", required=True)


def test_get_int_conversion_error(monkeypatch):
    monkeypatch.setenv("MY_INT", "notint")
    with pytest.raises(ConfigError):
        get_int("MY_INT", required=True)


def test_get_bool_true(monkeypatch):
    monkeypatch.setenv("FLAG", "yes")
    assert get_bool("FLAG") is True


def test_get_bool_default(monkeypatch):
    monkeypatch.delenv("FLAG", raising=False)
    assert get_bool("FLAG", default=True) is True
