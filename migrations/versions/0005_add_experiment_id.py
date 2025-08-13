"""Add experiment_id to model registry"""

from __future__ import annotations

from pathlib import Path

from alembic import op
import sqlalchemy as sa  # noqa:F401

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[1] / "005_add_experiment_id.sql"
    op.execute(sql_path.read_text())


def downgrade() -> None:
    op.execute("ALTER TABLE model_registry DROP COLUMN IF EXISTS experiment_id")
