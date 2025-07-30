from __future__ import annotations

import os
from typing import Iterable


def validate_required_env(vars: Iterable[str]) -> None:
    """Raise ``RuntimeError`` if any environment variable is missing."""
    missing = [var for var in vars if not os.getenv(var)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )


__all__ = ["validate_required_env"]
