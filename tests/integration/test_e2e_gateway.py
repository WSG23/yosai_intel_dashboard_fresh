import os
import shutil

import pytest
import requests
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


def get_total_requests(metrics: str) -> float:
    total = 0.0
    for line in metrics.splitlines():
        if line.startswith("yosai_request_total"):
            parts = line.split()
            if len(parts) == 2:
                try:
                    total += float(parts[1])
                except ValueError:
                    pass
    return total


@pytest.mark.integration
def test_gateway_end_to_end(tmp_path):
    if not shutil.which("docker"):
        pytest.skip("docker not available")

    with PostgresContainer("postgres:15-alpine") as pg, RedisContainer(
        "redis:7-alpine"
    ) as redis:
        pg_host = pg.get_container_host_ip()
        pg_port = pg.get_exposed_port(pg.port)
        redis_host = redis.get_container_host_ip()
        redis_port = redis.get_exposed_port(redis.port_to_expose)

        analytics_image = DockerContainer.from_dockerfile(
            ".", dockerfile="Dockerfile"
        ).build()
        analytics = (
            DockerContainer(analytics_image)
            .with_exposed_ports(8001)
            .with_env("YOSAI_ENV", "development")
            .with_env("DB_HOST", pg_host)
            .with_env("DB_PORT", pg_port)
            .with_env("DB_USER", pg.USERNAME)
            .with_env("DB_PASSWORD", pg.PASSWORD)
            .with_env("DB_NAME", pg.DBNAME)
            .with_env("REDIS_HOST", redis_host)
            .with_env("REDIS_PORT", redis_port)
            .with_command(
                "python -m uvicorn services.analytics_microservice.app:app --host 0.0.0.0 --port 8001"
            )
        )
        analytics.start()
        a_host = analytics.get_container_host_ip()
        a_port = analytics.get_exposed_port(8001)

        gateway_image = DockerContainer.from_dockerfile(
            ".", dockerfile="Dockerfile.gateway"
        ).build()
        gateway = (
            DockerContainer(gateway_image)
            .with_exposed_ports(8080)
            .with_env("APP_HOST", a_host)
            .with_env("APP_PORT", a_port)
            .with_env("DB_HOST", pg_host)
            .with_env("DB_PORT", pg_port)
            .with_env("DB_USER", pg.USERNAME)
            .with_env("DB_PASSWORD", pg.PASSWORD)
            .with_env("DB_GATEWAY_NAME", pg.DBNAME)
            .with_env("REDIS_HOST", redis_host)
            .with_env("REDIS_PORT", redis_port)
        )
        gateway.start()
        g_host = gateway.get_container_host_ip()
        g_port = gateway.get_exposed_port(8080)

        metrics_url = f"http://{g_host}:{g_port}/metrics"
        start_metrics = requests.get(metrics_url, timeout=30)
        start_total = get_total_requests(start_metrics.text)

        resp = requests.get(
            f"http://{g_host}:{g_port}/api/v1/analytics/dashboard-summary",
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "success"

        end_metrics = requests.get(metrics_url, timeout=30)
        end_total = get_total_requests(end_metrics.text)
        assert end_total > start_total

        gateway.stop()
        analytics.stop()
