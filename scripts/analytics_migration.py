"""Utilities to migrate analytics to the centralized architecture."""

from pathlib import Path


def execute_migration(root: Path = Path(__file__).resolve().parent.parent) -> None:
    """Create required directories and stub files for analytics_core."""
    (root / "analytics_core").mkdir(exist_ok=True)
    for sub in ["services", "callbacks", "utils", "protocols", "config"]:
        (root / "analytics_core" / sub).mkdir(exist_ok=True)
    # This function intentionally does not modify existing files.
    print("analytics_core directory structure ensured")


__all__ = ["execute_migration"]
