"""Create outbox table for event sourcing"""

from __future__ import annotations

from pathlib import Path

from alembic import op
import sqlalchemy as sa  # noqa: F401


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[1] / "006_create_outbox_table.sql"
    with op.get_context().autocommit_block():
        op.execute(sql_path.read_text())


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_outbox_published_at")
    op.execute("DROP TABLE IF EXISTS outbox")

