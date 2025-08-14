"""Add indexes based on query log analysis"""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa  # noqa:F401
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[1] / "004_add_missing_indexes.sql"
    with op.get_context().autocommit_block():
        op.execute(sql_path.read_text())


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_incident_tickets_status")
    op.execute("DROP INDEX IF EXISTS idx_anomaly_detections_type")
    op.execute("DROP INDEX IF EXISTS idx_anomaly_detections_detected_at")
    op.execute("DROP INDEX IF EXISTS idx_access_events_timestamp")
