"""Add composite indexes for common access_event lookups"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa  # noqa:F401
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[1] / "007_add_composite_indexes.sql"
    with op.get_context().autocommit_block():
        op.execute(sql_path.read_text())


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_access_events_door_timestamp")
    op.execute("DROP INDEX IF EXISTS idx_access_events_person_timestamp")
