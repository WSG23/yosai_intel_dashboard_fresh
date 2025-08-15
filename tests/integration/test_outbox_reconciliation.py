from __future__ import annotations

import asyncio
import os
import shutil
import uuid
from datetime import datetime, timezone

import pytest
from testcontainers.postgres import PostgresContainer


@pytest.mark.integration
def test_outbox_reconciliation():
    """Events written via the repository should be processed by reconciliation."""

    if not shutil.which("docker"):
        pytest.skip("docker not available")

    image = "timescale/timescaledb:2.14.2-pg15"
    with PostgresContainer(image) as pg:
        dsn = pg.get_connection_url()
        os.environ.setdefault("VAULT_ADDR", "http://localhost")
        os.environ.setdefault("VAULT_TOKEN", "dev")

        from yosai_intel_dashboard.src.services.timescale.manager import (
            TimescaleDBManager,
        )
        from repositories.outbox_repository import OutboxRepository
        from services.migration.reconciliation import reconcile_outbox

        manager = TimescaleDBManager(dsn)
        repo = OutboxRepository(manager)
        asyncio.run(manager.connect())

        event = {
            "time": datetime.now(timezone.utc),
            "event_id": uuid.uuid4(),
            "person_id": "p1",
            "door_id": "d1",
            "facility_id": "f1",
            "access_result": "granted",
            "badge_status": "active",
            "response_time_ms": 5,
            "metadata": {},
        }

        asyncio.run(repo.save_access_event(event))
        assert asyncio.run(repo.pending_events()) == 1
        # unprocessed events can be retrieved for further processing
        pending = asyncio.run(repo.unprocessed_events())
        assert len(pending) == 1

        divergences = asyncio.run(reconcile_outbox(manager))
        assert divergences == 0
        assert asyncio.run(repo.pending_events()) == 0

        asyncio.run(manager.close())
