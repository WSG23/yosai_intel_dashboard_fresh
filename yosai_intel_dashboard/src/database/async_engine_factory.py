"""Utilities for building async database engines with driver selection."""

from __future__ import annotations

from importlib import import_module

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from yosai_intel_dashboard.src.infrastructure.config import DatabaseSettings


def _module_available(name: str) -> bool:
    try:
        import_module(name)
        return True
    except Exception:
        return False


def get_asyncpg_driver() -> str:
    """Return the preferred async PostgreSQL driver.

    Prefers ``asyncpg`` when available, otherwise falls back to ``psycopg``
    which offers native asyncio support. Raises ``RuntimeError`` if no
    suitable driver is installed.
    """

    if _module_available("asyncpg"):
        return "asyncpg"
    if _module_available("psycopg"):
        return "psycopg"
    raise RuntimeError("No async PostgreSQL driver available")


def build_async_engine(cfg: DatabaseSettings) -> AsyncEngine:
    """Create an ``AsyncEngine`` using the best available driver."""

    url = cfg.get_connection_string()
    if cfg.type.lower() in {"postgresql", "postgres"}:
        driver = get_asyncpg_driver()
        url = url.replace("postgresql://", f"postgresql+{driver}://")

    return create_async_engine(
        url,
        pool_size=cfg.async_pool_min_size,
        max_overflow=max(cfg.async_pool_max_size - cfg.async_pool_min_size, 0),
        pool_timeout=cfg.async_connection_timeout,
    )


__all__ = ["build_async_engine", "get_asyncpg_driver"]
