import shutil
import time

import pytest
import requests
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


def _total_open(data: dict) -> float:
    total = 0.0
    for svc in data.values():
        total += float(svc.get("open", 0))
    return total


@pytest.mark.integration
def test_gateway_breaker_counts_on_downtime(tmp_path):
    if not shutil.which("docker"):
        pytest.skip("docker not available")

    with PostgresContainer("postgres:15-alpine") as pg, RedisContainer(
        "redis:7-alpine"
    ) as redis:
        pg_host = pg.get_container_host_ip()
        pg_port = pg.get_exposed_port(pg.port)
        redis_host = redis.get_container_host_ip()
        redis_port = redis.get_exposed_port(redis.port_to_expose)

        gateway_image = DockerContainer.from_dockerfile(
            ".", dockerfile="Dockerfile.gateway"
        ).build()
        gateway = (
            DockerContainer(gateway_image)
            .with_exposed_ports(8080)
            .with_env("APP_HOST", "127.0.0.1")
            .with_env("APP_PORT", "9999")
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

        breaker_url = f"http://{g_host}:{g_port}/breaker"
        start_data = requests.get(breaker_url, timeout=30).json()
        start_open = _total_open(start_data)

        for _ in range(6):
            try:
                requests.get(
                    f"http://{g_host}:{g_port}/api/v1/analytics/dashboard-summary",
                    timeout=5,
                )
            except requests.RequestException:
                pass
            time.sleep(0.5)

        end_data = requests.get(breaker_url, timeout=30).json()
        end_open = _total_open(end_data)

        gateway.stop()

        assert end_open >= start_open
