# coding: utf-8
"""End-to-end integration tests for upload and analytics pipeline.

This module spins up ephemeral PostgreSQL and Redis services using
``docker-compose`` through the ``testcontainers`` library.  A tiny
``FastAPI`` application implements an upload -> process -> analytics
flow with very small pieces of logic so that the behaviour can be
verified without relying on the full project stack.

The scenarios covered:
* Upload file, trigger processing and query analytics results.
* Authentication and simple RBAC checks.
* Error handling for a corrupted upload and retry behaviour when the
  message broker is temporarily unavailable.
* A light load test to ensure multiple concurrent uploads are handled
  within reasonable time.

The tests are skipped automatically when the runtime environment does
not provide a Docker engine capable of running ``docker-compose``.
"""

from __future__ import annotations

import concurrent.futures
import shutil
import subprocess
import time
from typing import Any, Callable

import psycopg2
import pytest
import redis
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.testclient import TestClient
from testcontainers.compose import DockerCompose

from yosai_intel_dashboard.src.infrastructure.config.connection_retry import (
    ConnectionRetryManager,
    RetryConfig,
)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

USERS = {
    "token-uploader": "uploader",
    "token-analyst": "analyst",
    "token-admin": "admin",
}


def _check_docker_available() -> bool:
    """Return True if docker and docker compose are available."""
    if not shutil.which("docker"):
        return False
    try:
        # ``docker compose`` is available with recent docker versions.  If the
        # command fails we will attempt to fall back to ``docker-compose``.
        subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return bool(shutil.which("docker-compose"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def compose(tmp_path_factory):
    """Start postgres and redis using a temporary docker-compose file."""
    if not _check_docker_available():  # pragma: no cover - depends on host
        pytest.skip("docker compose not available")

    compose_dir = tmp_path_factory.mktemp("compose")
    compose_file = compose_dir / "docker-compose.yml"
    compose_file.write_text(
        """
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: testdb
    ports:
      - '5432'
  broker:
    image: redis:7-alpine
    ports:
      - '6379'
"""
    )

    with DockerCompose(str(compose_dir), compose_file_name="docker-compose.yml") as dc:
        yield dc


@pytest.fixture
def app_client(compose):
    """Provide a FastAPI app connected to the temporary services."""
    db_host = compose.get_service_host("db", 5432)
    db_port = int(compose.get_service_port("db", 5432))
    redis_host = compose.get_service_host("broker", 6379)
    redis_port = int(compose.get_service_port("broker", 6379))

    retry = ConnectionRetryManager(
        RetryConfig(max_attempts=5, base_delay=0.5, jitter=False)
    )

    def _connect_db():
        return psycopg2.connect(
            host=db_host, port=db_port, user="user", password="pass", dbname="testdb"
        )

    db = retry.run_with_retry(_connect_db)
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS analytics(id SERIAL PRIMARY KEY, rows INT)")
    cur.execute("TRUNCATE analytics")
    db.commit()

    def _connect_redis():
        return redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    r = retry.run_with_retry(_connect_redis)
    r.flushall()

    app, process_once = _create_app(db, r)
    app.state.process_once = process_once

    client = TestClient(app)
    try:
        yield client, app
    finally:
        client.close()
        r.close()
        db.close()


# ---------------------------------------------------------------------------
# Application under test
# ---------------------------------------------------------------------------


def _create_app(db: Any, broker: redis.Redis) -> tuple[FastAPI, Callable[[], bool]]:
    app = FastAPI()
    retry = ConnectionRetryManager(
        RetryConfig(max_attempts=3, base_delay=0.1, jitter=False)
    )
    app.state.db = db
    app.state.redis = broker
    app.state.retry = retry

    def auth(authorization: str | None = Header(None)) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401)
        token = authorization.split()[1]
        role = USERS.get(token)
        if role is None:
            raise HTTPException(status_code=401)
        return role

    @app.post("/upload")
    async def upload_file(
        file: UploadFile = File(...),
        role: str = Depends(auth),
    ):
        if role not in {"uploader", "admin"}:
            raise HTTPException(status_code=403)
        data = await file.read()
        if b"," not in data:
            raise HTTPException(status_code=400, detail="corrupted")
        text = data.decode()

        def push():
            app.state.redis.lpush("uploads", text)

        app.state.retry.run_with_retry(push)
        return {"status": "queued"}

    def process_once() -> bool:
        item = app.state.redis.rpop("uploads")
        if item is None:
            return False
        lines = item.strip().splitlines()
        rows = max(len(lines) - 1, 0)
        cur = app.state.db.cursor()
        cur.execute("INSERT INTO analytics(rows) VALUES (%s)", (rows,))
        app.state.db.commit()
        return True

    @app.get("/analytics")
    def get_analytics(role: str = Depends(auth)):
        if role not in {"analyst", "admin"}:
            raise HTTPException(status_code=403)
        cur = app.state.db.cursor()
        cur.execute("SELECT COALESCE(SUM(rows),0) FROM analytics")
        total = cur.fetchone()[0]
        return {"rows": total}

    return app, process_once


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_upload_process_and_analytics(app_client):
    client, app = app_client
    files = {"file": ("data.csv", "a,b\n1,2\n3,4\n")}
    resp = client.post(
        "/upload", files=files, headers={"Authorization": "Bearer token-uploader"}
    )
    assert resp.status_code == 200

    while app.state.process_once():
        pass

    resp = client.get(
        "/analytics", headers={"Authorization": "Bearer token-analyst"}
    )
    assert resp.status_code == 200
    assert resp.json()["rows"] == 2


@pytest.mark.integration
def test_authentication_and_rbac(app_client):
    client, _ = app_client
    files = {"file": ("data.csv", "a,b\n1,2\n")}

    resp = client.post("/upload", files=files)
    assert resp.status_code == 401

    resp = client.get(
        "/analytics", headers={"Authorization": "Bearer token-uploader"}
    )
    assert resp.status_code == 403


@pytest.mark.integration
def test_corrupted_upload_and_retry(app_client, monkeypatch):
    client, app = app_client

    # Corrupted upload (missing comma)
    files = {"file": ("data.csv", "invalid data")}
    resp = client.post(
        "/upload", files=files, headers={"Authorization": "Bearer token-uploader"}
    )
    assert resp.status_code == 400

    # Simulate broker outage for first attempt
    calls = {"n": 0}
    original = app.state.redis.lpush

    def flaky(key: str, value: str):
        calls["n"] += 1
        if calls["n"] == 1:
            raise redis.exceptions.ConnectionError("down")
        return original(key, value)

    monkeypatch.setattr(app.state.redis, "lpush", flaky)

    files = {"file": ("data.csv", "a,b\n1,2\n")}
    resp = client.post(
        "/upload", files=files, headers={"Authorization": "Bearer token-uploader"}
    )
    assert resp.status_code == 200
    assert calls["n"] >= 2  # retried

    while app.state.process_once():
        pass

    resp = client.get(
        "/analytics", headers={"Authorization": "Bearer token-analyst"}
    )
    assert resp.json()["rows"] >= 1


@pytest.mark.integration
def test_load_concurrency(app_client):
    client, app = app_client

    def send(idx: int):
        content = f"a,b\n{idx},2\n"
        files = {"file": (f"data{idx}.csv", content)}
        return client.post(
            "/upload", files=files, headers={"Authorization": "Bearer token-uploader"}
        )

    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        responses = list(ex.map(send, range(5)))
    duration = time.perf_counter() - start
    assert all(r.status_code == 200 for r in responses)
    assert duration < 5  # basic throughput check

    while app.state.process_once():
        pass

    resp = client.get(
        "/analytics", headers={"Authorization": "Bearer token-analyst"}
    )
    assert resp.json()["rows"] == 5
