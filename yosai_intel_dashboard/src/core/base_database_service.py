"""Lightweight database connection service."""

from __future__ import annotations

import logging
from typing import Optional

from yosai_intel_dashboard.src.infrastructure.config import DatabaseSettings


class BaseDatabaseService:
    """Simplified database connector supporting multiple backends."""

    def __init__(self, config: Optional[DatabaseSettings] = None) -> None:
        """Create a connection using the provided ``DatabaseSettings``."""
        self.config = config or DatabaseSettings()
        self.log = logging.getLogger(self.__class__.__name__)
        self.connection = self._create_connection()

    # ---------------------------------------------------------------
    def _create_connection(self):
        db_type = (self.config.type or "").lower()

        if db_type in {"postgresql", "postgres", "pg"}:
            try:
                import psycopg2
            except ImportError as exc:  # pragma: no cover - optional dep
                raise ImportError(
                    "psycopg2 is required for PostgreSQL support"
                ) from exc

            return psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                dbname=self.config.name,
                user=self.config.user,
                password=self.config.password,
                connect_timeout=self.config.connection_timeout,
            )

        if db_type in {"mysql", "mariadb"}:
            try:
                import pymysql
            except ImportError as exc:  # pragma: no cover - optional dep
                raise ImportError("pymysql is required for MySQL support") from exc

            return pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                db=self.config.name,
                user=self.config.user,
                password=self.config.password,
                connect_timeout=self.config.connection_timeout,
            )

        if db_type in {"mongodb", "mongo"}:
            try:
                from pymongo import MongoClient  # type: ignore
            except Exception as exc:  # pragma: no cover - optional dep
                raise ImportError("pymongo is required for MongoDB support") from exc

            return MongoClient(
                host=self.config.host,
                port=self.config.port,
                username=self.config.user or None,
                password=self.config.password or None,
                serverSelectionTimeoutMS=self.config.connection_timeout * 1000,
            )

        if db_type == "redis":
            try:
                import redis
            except ImportError as exc:  # pragma: no cover - optional dep
                raise ImportError(
                    "redis package is required for Redis support"
                ) from exc

            return redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password or None,
                socket_connect_timeout=self.config.connection_timeout,
            )

        raise ValueError(f"Unsupported database type: {self.config.type}")

    # ---------------------------------------------------------------
    def close(self) -> None:
        if self.connection and hasattr(self.connection, "close"):
            try:
                self.connection.close()
            except Exception:  # pragma: no cover - best effort
                pass


__all__ = ["BaseDatabaseService"]
