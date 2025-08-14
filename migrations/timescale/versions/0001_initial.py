"""Timescale initial schema"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa  # noqa:F401
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    base = Path(__file__).resolve().parents[1]
    with op.get_context().autocommit_block():
        for fname in [
            "001_create_hypertables.sql",
            "002_create_continuous_aggregates.sql",
            "003_setup_compression.sql",
            "004_retention_policies.sql",
        ]:
            op.execute((base / fname).read_text())


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS access_events_5min")
    op.execute("DROP TABLE IF EXISTS access_events")
    op.execute("DROP EXTENSION IF EXISTS timescaledb")
