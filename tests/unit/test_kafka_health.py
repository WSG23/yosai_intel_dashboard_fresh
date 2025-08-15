import sys
import types

from yosai_intel_dashboard.src.infrastructure.monitoring import kafka_health as kh


class DummyBroker:
    def __init__(self, id, host="localhost", port=9092):
        self.id = id
        self.host = host
        self.port = port


class DummyPartition:
    def __init__(self, pid, replicas, isrs):
        self.id = pid
        self.replicas = list(range(replicas))
        self.isrs = list(range(isrs))


class DummyTopic:
    def __init__(self, name, partitions):
        self.topic = name
        self.partitions = {p.id: p for p in partitions}


class DummyMeta:
    def __init__(self, brokers, topics):
        self.brokers = {b.id: b for b in brokers}
        self.topics = {t.topic: t for t in topics}


class DummyTopicPartition:
    def __init__(self, topic, partition):
        self.topic = topic
        self.partition = partition


class DummyAdmin:
    def __init__(self, meta):
        self._meta = meta
        self.consumer_groups = ["g1"]
        self.offsets = {
            "g1": {DummyTopicPartition("t", 0): types.SimpleNamespace(offset=5)}
        }

    def list_topics(self, timeout=5):
        return self._meta

    def list_consumer_groups(self, timeout=5):
        return [(g, None) for g in self.consumer_groups]

    def list_consumer_group_offsets(self, group, timeout=5):
        return self.offsets[group]


class DummyConsumer:
    def __init__(self, watermarks):
        self.watermarks = watermarks
        self.closed = False

    def get_watermark_offsets(self, tp, timeout=5):
        return (0, self.watermarks.get((tp.topic, tp.partition), 0))

    def close(self):
        self.closed = True


def test_check_cluster_health(monkeypatch):
    meta = DummyMeta([DummyBroker(1)], [DummyTopic("t", [DummyPartition(0, 2, 2)])])
    admin = DummyAdmin(meta)
    monkeypatch.setattr(kh, "AdminClient", lambda cfg: admin)
    monkeypatch.setattr(kh, "Consumer", lambda cfg: DummyConsumer({("t", 0): 10}))

    health = kh.check_cluster_health("b:9092")

    assert health["brokers"] == [{"id": 1, "host": "localhost", "port": 9092}]
    assert not health["topics"]["t"]["under_replicated"]
    assert health["consumer_lag"]["g1"]["t-0"] == 5
