"""Utilities to migrate to the new validation package."""
from pathlib import Path


def execute_migration(root: Path = Path(__file__).resolve().parent.parent) -> None:
    """Ensure the ``validation`` package exists and provide instructions."""
    (root / "validation").mkdir(exist_ok=True)
    print("validation package directory ensured")
    print("Update imports: 'from validation.security_validator import SecurityValidator'")


__all__ = ["execute_migration"]
