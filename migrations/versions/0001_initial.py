"""Initial schema using TimescaleDB"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa  # noqa:F401
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[1] / "001_init.sql"
    with op.get_context().autocommit_block():
        op.execute(sql_path.read_text())


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS access_events_5min")
    op.execute("DROP TABLE IF EXISTS emergency_lockdowns")
    op.execute("DROP TABLE IF EXISTS anti_passback_state")
    op.execute("DROP TABLE IF EXISTS time_restrictions")
    op.execute("DROP TABLE IF EXISTS access_blocklist")
    op.execute("DROP TABLE IF EXISTS access_permissions")
    op.execute("DROP TABLE IF EXISTS person_roles")
    op.execute("DROP TABLE IF EXISTS door_groups")
    op.execute("DROP TABLE IF EXISTS access_events")
    op.execute("DROP EXTENSION IF EXISTS timescaledb")
