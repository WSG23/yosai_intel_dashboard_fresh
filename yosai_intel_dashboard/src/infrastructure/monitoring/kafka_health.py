from __future__ import annotations

"""Kafka cluster health utilities."""

from typing import Any, Dict, List

from confluent_kafka import Consumer
from confluent_kafka.admin import AdminClient

# ----------------------------------------------------------------------


def _broker_status(client: AdminClient) -> List[Dict[str, Any]]:
    """Return basic information about brokers in the cluster."""
    meta = client.list_topics(timeout=5)
    return [{"id": b.id, "host": b.host, "port": b.port} for b in meta.brokers.values()]


# ----------------------------------------------------------------------


def _topic_replication(client: AdminClient) -> Dict[str, Any]:
    """Return replication health for each topic."""
    meta = client.list_topics(timeout=5)
    topics: Dict[str, Any] = {}
    for topic in meta.topics.values():
        parts = []
        under_replicated = False
        for p in topic.partitions.values():
            part_ur = len(p.isrs) < len(p.replicas)
            parts.append(
                {
                    "partition": p.id,
                    "replicas": len(p.replicas),
                    "in_sync_replicas": len(p.isrs),
                    "under_replicated": part_ur,
                }
            )
            under_replicated |= part_ur
        topics[topic.topic] = {
            "under_replicated": under_replicated,
            "partitions": parts,
        }
    return topics


# ----------------------------------------------------------------------


def _consumer_lag(client: AdminClient, brokers: str) -> Dict[str, Dict[str, int]]:
    """Estimate consumer lag for each consumer group."""
    groups = [g[0] for g in client.list_consumer_groups(timeout=5)]
    if not groups:
        return {}

    consumer = Consumer(
        {
            "bootstrap.servers": brokers,
            "group.id": "health-check",  # temporary group
            "enable.auto.commit": False,
        }
    )
    lag: Dict[str, Dict[str, int]] = {}
    try:
        for group in groups:
            offsets = client.list_consumer_group_offsets(group, timeout=5)
            part_lag: Dict[str, int] = {}
            for tp, data in offsets.items():
                try:
                    lo, hi = consumer.get_watermark_offsets(tp, timeout=5)
                except Exception:
                    continue
                current = data.offset if hasattr(data, "offset") else data
                part_lag[f"{tp.topic}-{tp.partition}"] = max(hi - current, 0)
            lag[group] = part_lag
    finally:
        consumer.close()
    return lag


# ----------------------------------------------------------------------


def check_cluster_health(brokers: str = "localhost:9092") -> Dict[str, Any]:
    """Return health information about the Kafka cluster."""
    client = AdminClient({"bootstrap.servers": brokers})
    return {
        "brokers": _broker_status(client),
        "topics": _topic_replication(client),
        "consumer_lag": _consumer_lag(client, brokers),
    }


__all__ = ["check_cluster_health"]
