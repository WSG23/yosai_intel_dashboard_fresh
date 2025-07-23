"""Initial schema for analytics database"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa  # noqa:F401

revision = "analytics_0001"
down_revision = None
branch_labels = ("analytics_db",)
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TABLE IF NOT EXISTS analytics_dummy(id SERIAL PRIMARY KEY)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS analytics_dummy")
