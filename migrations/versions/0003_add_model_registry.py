"""Add model registry table"""
from __future__ import annotations
from pathlib import Path
from alembic import op
import sqlalchemy as sa  # noqa:F401

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[1] / "003_add_model_registry.sql"
    op.execute(sql_path.read_text())


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ml_models")
