import json
import time
from datetime import datetime
from pathlib import Path

import pytest
import requests
from kafka import KafkaConsumer
from testcontainers.core.container import DockerContainer


def wait_for_service(url: str, timeout: int = 60) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code < 500:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"service {url} not ready")


@pytest.mark.integration
def test_publish_event_via_gateway(tmp_path, kafka_service):
    service_script = Path(__file__).with_name("mock_event_service.py")
    event_service = (
        DockerContainer("python:3.11-slim")
        .with_network_mode("host")
        .with_env("KAFKA_BROKERS", kafka_service)
        .with_volume_mapping(str(service_script), "/app/service.py")
        .with_command(
            'sh -c "pip install fastapi uvicorn kafka-python >/tmp/pip.log && '
            'uvicorn service:app --host 0.0.0.0 --port 5000"'
        )
    )
    with event_service:
        wait_for_service("http://localhost:5000/health")

        gateway_image = DockerContainer.from_dockerfile(
            Path(".").resolve(), dockerfile="docker/Dockerfile.gateway"
        ).build()
        gateway = (
            DockerContainer(gateway_image)
            .with_network_mode("host")
            .with_env("APP_HOST", "localhost")
            .with_env("APP_PORT", "5000")
        )
        with gateway:
            wait_for_service("http://localhost:8080/health")

            event = {
                "event_id": "1",
                "timestamp": datetime.utcnow().isoformat(),
                "person_id": "p1",
                "door_id": "d1",
                "access_result": "Granted",
            }
            resp = requests.post(
                "http://localhost:8080/api/v1/events", json=event, timeout=30
            )
            assert resp.status_code == 200

            consumer = KafkaConsumer(
                "access-events",
                bootstrap_servers=kafka_service,
                group_id=f"test-{time.time()}",
                auto_offset_reset="earliest",
                consumer_timeout_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            msgs = [msg.value for msg in consumer]
            assert any(m.get("event_id") == "1" for m in msgs)
            consumer.close()
