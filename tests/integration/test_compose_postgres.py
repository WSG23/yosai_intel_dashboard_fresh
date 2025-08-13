from __future__ import annotations

import shutil
import subprocess
import psycopg2
import pytest
from testcontainers.compose import DockerCompose


def _docker_compose_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return bool(shutil.which("docker-compose"))


@pytest.mark.integration
@pytest.mark.skipif(not _docker_compose_available(), reason="docker compose not available")
def test_postgres_service(tmp_path_factory):
    compose_dir = tmp_path_factory.mktemp("compose")
    compose_file = compose_dir / "docker-compose.yml"
    compose_file.write_text(
        """
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: testdb
    ports:
      - '5432'
"""
    )
    with DockerCompose(str(compose_dir), compose_file_name="docker-compose.yml") as dc:
        host = dc.get_service_host("db", 5432)
        port = int(dc.get_service_port("db", 5432))
        conn = psycopg2.connect(host=host, port=port, user="postgres", password="pass", dbname="testdb")
        cur = conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        conn.close()
