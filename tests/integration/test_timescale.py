from __future__ import annotations

import os
import pathlib
import shutil
import uuid
from datetime import datetime, timedelta, timezone

import alembic.command
import alembic.config
import psycopg2
import pytest
from psycopg2.extras import execute_batch
from testcontainers.postgres import PostgresContainer


@pytest.mark.integration
def test_timescale_policies(tmp_path):
    if not shutil.which("docker"):
        pytest.skip("docker not available")

    image = "timescale/timescaledb:2.14.2-pg15"
    with PostgresContainer(image) as pg:
        dsn = pg.get_connection_url()
        os.environ["TIMESCALE_DSN"] = dsn

        cfg = alembic.config.Config(
            str(
                (
                    pathlib.Path(__file__).resolve().parents[2]
                    / "migrations"
                    / "timescale"
                    / "alembic.ini"
                )
            )
        )
        alembic.command.upgrade(cfg, "head")

        conn = psycopg2.connect(dsn)
        cur = conn.cursor()

        base_time = datetime.now(timezone.utc) - timedelta(days=100)
        rows = [
            (
                base_time + timedelta(minutes=i),
                str(uuid.uuid4()),
                f"person-{i%3}",
                f"door-{i%5}",
                f"fac-{i%2}",
                "granted",
                "active",
                i,
                "{}",
            )
            for i in range(200)
        ]
        execute_batch(
            cur,
            "INSERT INTO access_events (time, event_id, person_id, door_id, facility_id, access_result, badge_status, response_time_ms, metadata) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            rows,
        )
        conn.commit()

        cur.execute(
            "CALL refresh_continuous_aggregate('access_events_5min', NULL, NULL)"
        )
        cur.execute("SELECT COUNT(*) FROM access_events_5min")
        assert cur.fetchone()[0] > 0

        cur.execute(
            "SELECT job_id FROM timescaledb_information.jobs WHERE hypertable_name='access_events' AND proc_name='policy_compression'"
        )
        job = cur.fetchone()[0]
        cur.execute(f"SELECT run_job({job})")
        conn.commit()

        cur.execute(
            "SELECT is_compressed FROM timescaledb_information.chunks WHERE hypertable_name='access_events' LIMIT 1"
        )
        assert cur.fetchone()[0]

        cur.execute(
            "SELECT job_id FROM timescaledb_information.jobs WHERE hypertable_name='access_events' AND proc_name='policy_retention'"
        )
        job = cur.fetchone()[0]
        cur.execute(f"SELECT run_job({job})")
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM access_events")
        assert cur.fetchone()[0] == 0

        cur.close()
        conn.close()
