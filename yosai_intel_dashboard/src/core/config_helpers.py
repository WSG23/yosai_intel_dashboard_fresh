import os
from typing import Optional  # noqa: F401


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def get_max_display_rows(default: int = 200) -> int:
    """
    Lightweight helper that reads MAX_DISPLAY_ROWS from the environment.
    It must not import any other project modules to avoid circular imports.
    """
    return _int_env("MAX_DISPLAY_ROWS", default)
