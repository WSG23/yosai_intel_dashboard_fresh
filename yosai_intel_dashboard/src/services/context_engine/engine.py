"""Flink based context correlation engine.

The real deployment runs a PyFlink job that joins security and
environmental event streams.  For unit tests and lightweight deployments
where ``pyflink`` is unavailable we fall back to a small in memory
implementation that mimics the behaviour of the streaming job.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Dict, Any, Optional

from optional_dependencies import import_optional

# Optional imports -- these resolve to ``None`` when pyflink is not installed.
StreamExecutionEnvironment = import_optional(
    "pyflink.datastream.StreamExecutionEnvironment"
)
EnvironmentSettings = import_optional("pyflink.table.EnvironmentSettings")
StreamTableEnvironment = import_optional("pyflink.table.StreamTableEnvironment")


@dataclass
class SecurityEvent:
    """Simplified security event."""

    device_id: str
    ts: datetime
    threat_level: int
    factor: str


@dataclass
class EnvironmentalEvent:
    """Simplified environmental event."""

    device_id: str
    ts: datetime
    temperature: float
    humidity: float


class ContextEngine:
    """Join security and environmental streams to produce enriched alerts.

    Parameters
    ----------
    producer:
        Object with a ``produce(topic, value, *args, **kwargs)`` method used to
        publish alerts.  In production this is typically a Kafka producer while
        tests can provide a lightweight stub.
    alert_topic:
        Destination Kafka topic for enriched alerts.
    window_size:
        Correlation window in seconds used when matching events.
    """

    def __init__(self, producer: Any, alert_topic: str, window_size: int = 30) -> None:
        self.producer = producer
        self.alert_topic = alert_topic
        self.window_size = window_size

    # ------------------------------------------------------------------
    # Lightweight implementation used in tests
    def process_events(
        self,
        security_events: Iterable[SecurityEvent],
        environmental_events: Iterable[EnvironmentalEvent],
    ) -> List[Dict[str, Any]]:
        """Correlate ``security_events`` with ``environmental_events``.

        The implementation performs a naive windowed join and applies a couple
        of tiny CEP inspired rules: a confidence score based on threat level
        and number of matching environmental events and a simple conflict
        resolution that favours the most recent environmental reading.
        """

        env_by_device: Dict[str, List[EnvironmentalEvent]] = {}
        for ev in environmental_events:
            env_by_device.setdefault(ev.device_id, []).append(ev)

        alerts: List[Dict[str, Any]] = []
        for sec in security_events:
            envs = [
                e
                for e in env_by_device.get(sec.device_id, [])
                if abs((e.ts - sec.ts).total_seconds()) <= self.window_size
            ]
            if not envs:
                continue
            # Conflict resolution – choose latest env event
            env = max(envs, key=lambda e: e.ts)
            # Confidence score – bounded between 0 and 1
            confidence = min(1.0, (sec.threat_level / 10.0) + 0.1 * len(envs))
            alert = {
                "device_id": sec.device_id,
                "ts": sec.ts.isoformat(),
                "threat_level": sec.threat_level,
                "temperature": env.temperature,
                "humidity": env.humidity,
                "confidence": confidence,
            }
            self._publish(alert)
            alerts.append(alert)
        return alerts

    def _publish(self, alert: Dict[str, Any]) -> None:
        """Publish ``alert`` using the configured producer."""

        try:
            self.producer.produce(self.alert_topic, alert)
        except TypeError:
            # Fallback for KafkaProducer expecting ``value`` keyword
            self.producer.produce(topic=self.alert_topic, value=alert, value_schema=None)

    # ------------------------------------------------------------------
    # Flink job creation
    def build_flink_job(
        self,
        security_topic: str,
        environmental_topic: str,
        bootstrap_servers: str = "localhost:9092",
    ) -> None:
        """Run the Flink job that performs the real time correlation.

        The job definition uses the PyFlink Table API.  It creates sources for
        the security and environmental streams, joins them within the
        configured window and publishes enriched alerts to ``alert_topic``.
        The method blocks until job completion.
        """

        if not (
            StreamExecutionEnvironment and EnvironmentSettings and StreamTableEnvironment
        ):
            raise RuntimeError("pyflink is required to run the context engine job")

        env = StreamExecutionEnvironment.get_execution_environment()
        settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
        t_env = StreamTableEnvironment.create(env, environment_settings=settings)

        security_ddl = f"""
            CREATE TABLE security_events (
                device_id STRING,
                ts TIMESTAMP(3),
                threat_level INT,
                factor STRING,
                WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
            ) WITH (
                'connector' = 'kafka',
                'topic' = '{security_topic}',
                'properties.bootstrap.servers' = '{bootstrap_servers}',
                'format' = 'json'
            )
        """

        env_ddl = f"""
            CREATE TABLE environmental_events (
                device_id STRING,
                ts TIMESTAMP(3),
                temperature DOUBLE,
                humidity DOUBLE,
                WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
            ) WITH (
                'connector' = 'kafka',
                'topic' = '{environmental_topic}',
                'properties.bootstrap.servers' = '{bootstrap_servers}',
                'format' = 'json'
            )
        """

        sink_ddl = f"""
            CREATE TABLE enriched_alerts (
                device_id STRING,
                ts TIMESTAMP(3),
                threat_level INT,
                temperature DOUBLE,
                humidity DOUBLE,
                confidence DOUBLE
            ) WITH (
                'connector' = 'kafka',
                'topic' = '{self.alert_topic}',
                'properties.bootstrap.servers' = '{bootstrap_servers}',
                'format' = 'json'
            )
        """

        t_env.execute_sql(security_ddl)
        t_env.execute_sql(env_ddl)
        t_env.execute_sql(sink_ddl)

        query = f"""
            INSERT INTO enriched_alerts
            SELECT s.device_id,
                   s.ts,
                   s.threat_level,
                   e.temperature,
                   e.humidity,
                   LEAST(1.0, (s.threat_level / 10.0) + 0.1) as confidence
            FROM security_events s
            JOIN environmental_events e
            ON s.device_id = e.device_id
            AND e.ts BETWEEN s.ts - INTERVAL '{self.window_size}' SECOND AND s.ts + INTERVAL '{self.window_size}' SECOND
        """
        t_env.execute_sql(query).wait()


__all__ = ["ContextEngine", "SecurityEvent", "EnvironmentalEvent"]
