"""Flink job definitions for real-time analytics.

This module provides helper functions for defining PyFlink jobs that consume
events from Kafka, perform simple aggregations and publish the results back to
Kafka or to a relational database via the JDBC connector.  The functions here
do not start any infrastructure themselves; instead they produce jobs that can
be submitted to an existing Flink cluster.
"""

from __future__ import annotations

from typing import Optional

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import (
    EnvironmentSettings,
    StreamTableEnvironment,
)

__all__ = ["run_kafka_analytics_job", "run_kafka_to_database_job"]


def _create_table_environment() -> StreamTableEnvironment:
    """Create a streaming :class:`StreamTableEnvironment` instance.

    The helper centralises environment creation so that each job uses the same
    configuration.  A parallelism of ``1`` is set for deterministic examples.
    """

    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    return StreamTableEnvironment.create(env, environment_settings=settings)


def run_kafka_analytics_job(
    input_topic: str,
    output_topic: str,
    bootstrap_servers: str,
) -> None:
    """Run a Flink job that aggregates events and writes back to Kafka.

    The job expects JSON payloads with fields ``user_id``, ``action`` and
    ``ts`` (event timestamp).  It computes per-user counts and publishes the
    aggregated results to ``output_topic``.
    """

    t_env = _create_table_environment()

    source_ddl = f"""
        CREATE TABLE source_events (
            user_id STRING,
            action STRING,
            ts TIMESTAMP(3),
            WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = '{input_topic}',
            'properties.bootstrap.servers' = '{bootstrap_servers}',
            'properties.group.id' = 'flink-group',
            'format' = 'json',
            'scan.startup.mode' = 'earliest-offset'
        )
    """

    sink_ddl = f"""
        CREATE TABLE sink_events (
            user_id STRING,
            event_count BIGINT
        ) WITH (
            'connector' = 'kafka',
            'topic' = '{output_topic}',
            'properties.bootstrap.servers' = '{bootstrap_servers}',
            'format' = 'json'
        )
    """

    t_env.execute_sql(source_ddl)
    t_env.execute_sql(sink_ddl)

    t_env.execute_sql(
        """
        INSERT INTO sink_events
        SELECT user_id, COUNT(*) AS event_count
        FROM source_events
        GROUP BY user_id
        """
    ).wait()


def run_kafka_to_database_job(
    input_topic: str,
    bootstrap_servers: str,
    jdbc_url: str,
    table_name: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> None:
    """Run a Flink job that writes aggregated results to a database.

    Parameters
    ----------
    input_topic:
        Kafka topic containing JSON encoded events with ``user_id`` and
        ``ts`` fields.
    bootstrap_servers:
        Kafka bootstrap servers string, for example ``"kafka:9092"``.
    jdbc_url:
        JDBC connection URL for the target database.
    table_name:
        Name of the table where results should be inserted.
    username, password:
        Optional database credentials.  If provided they will be passed to the
        connector configuration.
    """

    t_env = _create_table_environment()

    auth_section = ""
    if username and password:
        auth_section = f"'username' = '{username}', 'password' = '{password}',"

    source_ddl = f"""
        CREATE TABLE source_events (
            user_id STRING,
            ts TIMESTAMP(3),
            WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = '{input_topic}',
            'properties.bootstrap.servers' = '{bootstrap_servers}',
            'properties.group.id' = 'flink-db-group',
            'format' = 'json',
            'scan.startup.mode' = 'earliest-offset'
        )
    """

    sink_ddl = f"""
        CREATE TABLE analytics_table (
            user_id STRING,
            event_count BIGINT
        ) WITH (
            'connector' = 'jdbc',
            'url' = '{jdbc_url}',
            'table-name' = '{table_name}',
            {auth_section}
            'driver' = 'org.postgresql.Driver'
        )
    """

    t_env.execute_sql(source_ddl)
    t_env.execute_sql(sink_ddl)

    t_env.execute_sql(
        """
        INSERT INTO analytics_table
        SELECT user_id, COUNT(*) AS event_count
        FROM source_events
        GROUP BY user_id
        """
    ).wait()
