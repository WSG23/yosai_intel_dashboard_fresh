import shutil
import subprocess

import pytest
import requests
from testcontainers.core.container import DockerContainer
from testcontainers.redis import RedisContainer


@pytest.mark.integration
def test_gateway_tls_connection(tmp_path):
    if not shutil.which("docker"):
        pytest.skip("docker not available")

    cert_dir = tmp_path / "certs"
    cert_dir.mkdir()
    cert_path = cert_dir / "server.crt"
    key_path = cert_dir / "server.key"
    subprocess.run(
        [
            "openssl",
            "req",
            "-new",
            "-x509",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-out",
            str(cert_path),
            "-keyout",
            str(key_path),
        ],
        check=True,
    )

    pg = (
        DockerContainer("bitnami/postgresql:15")
        .with_exposed_ports("5432")
        .with_env("POSTGRESQL_USERNAME", "testuser")
        .with_env("POSTGRESQL_PASSWORD", "testpass")
        .with_env("POSTGRESQL_DATABASE", "testdb")
        .with_env("POSTGRESQL_ENABLE_TLS", "yes")
        .with_env("POSTGRESQL_TLS_CERT_FILE", "/certs/server.crt")
        .with_env("POSTGRESQL_TLS_KEY_FILE", "/certs/server.key")
        .with_volume_mapping(str(cert_path), "/certs/server.crt")
        .with_volume_mapping(str(key_path), "/certs/server.key")
    )

    with pg as pg_container, RedisContainer("redis:7-alpine") as redis:
        pg_host = pg_container.get_container_host_ip()
        pg_port = pg_container.get_exposed_port("5432")
        redis_host = redis.get_container_host_ip()
        redis_port = redis.get_exposed_port(redis.port_to_expose)

        gateway_image = DockerContainer.from_dockerfile(
            ".", dockerfile="docker/Dockerfile.gateway"
        ).build()
        gateway = (
            DockerContainer(gateway_image)
            .with_exposed_ports(8080)
            .with_env("DB_HOST", pg_host)
            .with_env("DB_PORT", pg_port)
            .with_env("DB_USER", "testuser")
            .with_env("DB_PASSWORD", "testpass")
            .with_env("DB_GATEWAY_NAME", "testdb")
            .with_env("DB_SSLMODE", "require")
            .with_env("REDIS_HOST", redis_host)
            .with_env("REDIS_PORT", redis_port)
        )
        with gateway as gw:
            g_host = gw.get_container_host_ip()
            g_port = gw.get_exposed_port(8080)
            resp = requests.get(f"http://{g_host}:{g_port}/health", timeout=30)
            assert resp.status_code == 200
