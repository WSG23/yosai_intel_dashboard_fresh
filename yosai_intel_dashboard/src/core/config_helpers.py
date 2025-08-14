import os
from typing import Optional


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def get_max_display_rows(default: int = 200) -> int:
    return _int_env("MAX_DISPLAY_ROWS", default)
