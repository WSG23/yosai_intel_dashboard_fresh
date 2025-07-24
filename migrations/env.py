from __future__ import annotations

import configparser
import logging
import os
from logging.config import fileConfig
from typing import Iterable

from alembic import context
from sqlalchemy import engine_from_config, pool, text

config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger(__name__)

parser = configparser.ConfigParser()
parser.read(config.config_file_name)

for section in parser.sections():
    if section.endswith("_db"):
        env_var = f"{section[:-3].upper()}_DB_URL"
        override = os.getenv(env_var)
        if override:
            parser.set(section, "sqlalchemy.url", override)
            logger.info("Overriding %s URL from %s", section, env_var)


def _db_sections() -> Iterable[str]:
    for section in parser.sections():
        if section.endswith("_db"):
            yield section


def _ensure_timescale(connection) -> None:
    """Create TimescaleDB extension and hypertable if missing."""
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
    connection.execute(
        text(
            "SELECT create_hypertable('access_events', 'time', if_not_exists => TRUE)"
        )
    )


def run_migrations_offline() -> None:
    for section in _db_sections():
        url = parser.get(section, "sqlalchemy.url")
        context.configure(url=url, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online() -> None:
    for section in _db_sections():
        opts = {
            "sqlalchemy.url": parser.get(section, "sqlalchemy.url"),
        }
        connectable = engine_from_config(
            opts,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        with connectable.connect() as connection:
            _ensure_timescale(connection)
            context.configure(connection=connection)
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
