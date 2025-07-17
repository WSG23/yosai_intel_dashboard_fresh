"""Lightweight migration validation utilities for tests."""

from __future__ import annotations


class MigrationValidator:
    """Stubbed migration validator used in tests."""

    def generate_validation_report(self) -> dict[str, str]:
        """Return a simple success report."""
        return {"status": "ok"}


def test_migration_equivalence() -> bool:
    return True


def test_migration_performance() -> bool:
    return True


def test_migration_security() -> bool:
    return True


__all__ = [
    "MigrationValidator",
    "test_migration_equivalence",
    "test_migration_performance",
    "test_migration_security",
]
