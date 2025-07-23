"""Initial schema for events database"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa  # noqa:F401

revision = "events_0001"
down_revision = None
branch_labels = ("events_db",)
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TABLE IF NOT EXISTS events_dummy(id SERIAL PRIMARY KEY)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS events_dummy")
