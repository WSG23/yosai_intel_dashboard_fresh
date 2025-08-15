import json
import time
from datetime import datetime
from pathlib import Path

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


def wait_for_kafka(brokers: str = "localhost:9092", timeout: int = 60) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            KafkaConsumer(bootstrap_servers=brokers).close()
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Kafka not ready")


def test_publish_event_via_gateway(tmp_path):
    wait_for_kafka()
    service_script = Path(__file__).with_name("mock_event_service.py")
    event_service = (
        DockerContainer("python:3.11-slim")
        .with_exposed_ports(5000)
        .with_env("KAFKA_BROKERS", "host.docker.internal:9092")
        .with_volume_mapping(str(service_script), "/app/service.py")
        .with_command(
            "sh -c \"pip install fastapi uvicorn kafka-python >/tmp/pip.log && "
            "uvicorn service:app --host 0.0.0.0 --port 5000\""
        )
    )
    with event_service as svc:
        s_host = svc.get_container_host_ip()
        s_port = svc.get_exposed_port(5000)
        wait_for_service(f"http://{s_host}:{s_port}/health")

        gateway_image = DockerContainer.from_dockerfile(
            Path(".").resolve(), dockerfile="Dockerfile.gateway"
        ).build()
        gateway = (
            DockerContainer(gateway_image)
            .with_exposed_ports(8080)
            .with_env("APP_HOST", s_host)
            .with_env("APP_PORT", s_port)
        )
        with gateway as gw:
            g_host = gw.get_container_host_ip()
            g_port = gw.get_exposed_port(8080)
            wait_for_service(f"http://{g_host}:{g_port}/health")

            event = {
                "event_id": "1",
                "timestamp": datetime.utcnow().isoformat(),
                "person_id": "p1",
                "door_id": "d1",
                "access_result": "Granted",
            }
            resp = requests.post(
                f"http://{g_host}:{g_port}/api/v1/events", json=event, timeout=30
            )
            assert resp.status_code == 200

            consumer = KafkaConsumer(
                "access-events",
                bootstrap_servers="localhost:9092",
                group_id=f"test-{time.time()}",
                auto_offset_reset="earliest",
                consumer_timeout_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            msgs = [msg.value for msg in consumer]
            assert any(m.get("event_id") == "1" for m in msgs)
            consumer.close()
