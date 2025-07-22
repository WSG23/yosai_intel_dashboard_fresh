"""Add RBAC tables"""
from __future__ import annotations
from pathlib import Path
from alembic import op
import sqlalchemy as sa  # noqa:F401

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[2] / "002_add_rbac.sql"
    op.execute(sql_path.read_text())


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_roles")
    op.execute("DROP TABLE IF EXISTS role_permissions")
    op.execute("DROP TABLE IF EXISTS permissions")
    op.execute("DROP TABLE IF EXISTS roles")
