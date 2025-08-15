from __future__ import annotations

import shutil
from typing import Generator

import pytest

try:  # pragma: no cover - optional dependency in CI
    from testcontainers.kafka import KafkaContainer
except Exception:  # pragma: no cover - import error handled at runtime
    KafkaContainer = None


def _docker_available() -> bool:
    return shutil.which("docker") is not None


@pytest.fixture(scope="session")
def kafka_service() -> Generator[str, None, None]:
    """Provide an ephemeral Kafka broker for integration tests."""
    if KafkaContainer is None or not _docker_available():
        pytest.skip("docker or testcontainers not available")
    with KafkaContainer() as kafka:
        bootstrap = kafka.get_bootstrap_server().split("//", 1)[-1]
        yield bootstrap
