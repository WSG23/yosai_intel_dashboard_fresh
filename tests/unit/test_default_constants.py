from yosai_intel_dashboard.src.infrastructure.config import constants as constants


def test_default_ports():
    assert constants.DEFAULT_APP_PORT == 8050
    assert constants.DEFAULT_DB_PORT == 5432
    assert constants.DEFAULT_CACHE_PORT == 6379
