"""Timescale initial schema"""
from __future__ import annotations
from pathlib import Path
from alembic import op
import sqlalchemy as sa  # noqa:F401

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[3] / "scripts" / "init_timescaledb.sql"
    op.execute(sql_path.read_text())


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS access_events_5min")
    op.execute("DROP TABLE IF EXISTS access_events")
    op.execute("DROP EXTENSION IF EXISTS timescaledb")
