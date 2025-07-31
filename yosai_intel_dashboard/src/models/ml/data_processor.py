from __future__ import annotations

"""Scalable data processing pipeline with batch and stream support."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.config.constants import DEFAULT_CHUNK_SIZE
from yosai_intel_dashboard.src.utils.memory_utils import check_memory_limit

try:
    from confluent_kafka import Consumer, Producer
except Exception:  # pragma: no cover - optional dependency
    Consumer = Producer = None  # type: ignore

try:
    import multiprocessing as mp
except Exception:  # pragma: no cover - fallback single process
    mp = None  # type: ignore

# Ray is optional
try:
    import ray
except Exception:  # pragma: no cover - optional dependency
    ray = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class KafkaConfig:
    """Settings for Kafka integration."""

    brokers: str = "localhost:9092"
    topic: str = "events"
    group: str = "yosai-pipeline"
    auto_offset_reset: str = "latest"


@dataclass
class ProcessorConfig:
    """Configuration for :class:`DataProcessor`."""

    chunk_size: int = DEFAULT_CHUNK_SIZE
    max_memory_mb: int = 1024
    kafka: KafkaConfig = field(default_factory=KafkaConfig)
    enable_lineage: bool = True
    checkpoint_path: Path = Path("processor.checkpoint")
    use_ray: bool = False
    num_workers: int = 4


@dataclass
class LineageRecord:
    """Represents a processing step for lineage tracking."""

    step: str
    details: Dict[str, Any]


class DataProcessor:
    """Unified batch and streaming data processor."""

    def __init__(self, config: Optional[ProcessorConfig] = None) -> None:
        self.config = config or ProcessorConfig()
        self.lineage: List[LineageRecord] = []
        self._producer: Optional[Producer] = None
        self._consumer: Optional[Consumer] = None
        if Consumer and Producer:
            self._init_kafka()
        if self.config.use_ray and ray:
            if not ray.is_initialized():  # pragma: no cover - runtime check
                ray.init(ignore_reinit_error=True)

    # ------------------------------------------------------------------
    # Kafka initialization and helpers
    # ------------------------------------------------------------------
    def _init_kafka(self) -> None:
        """Initialize Kafka producer/consumer if libraries are available."""
        if not Producer or not Consumer:
            logger.warning("confluent_kafka not available; streaming disabled")
            return

        conf = {
            "bootstrap.servers": self.config.kafka.brokers,
            "group.id": self.config.kafka.group,
            "auto.offset.reset": self.config.kafka.auto_offset_reset,
        }
        try:
            self._producer = Producer(conf)
            self._consumer = Consumer(conf)
            self._consumer.subscribe([self.config.kafka.topic])
            logger.debug("Kafka client initialized")
        except Exception as exc:  # pragma: no cover - runtime error
            logger.error("Failed to initialize Kafka: %s", exc)
            self._producer = None
            self._consumer = None

    # ------------------------------------------------------------------
    # Lineage helpers
    # ------------------------------------------------------------------
    def _record_lineage(self, step: str, **details: Any) -> None:
        if not self.config.enable_lineage:
            return
        self.lineage.append(LineageRecord(step, details))

    # ------------------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------------------
    def process_file(self, path: str, *, parallel: bool = False) -> pd.DataFrame:
        """Load and process ``path`` in chunks, optionally in parallel."""
        chunks = []
        for i, chunk in enumerate(self._read_chunks(path)):
            self._record_lineage("read_chunk", index=i, rows=len(chunk))
            if parallel:
                processed = self._process_parallel([chunk])[0]
            else:
                processed = self._process_chunk(chunk)
            chunks.append(processed)
            self._write_checkpoint(i)
        df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        self._record_lineage("batch_complete", rows=len(df))
        return df

    def _read_chunks(self, path: str) -> Iterable[pd.DataFrame]:
        reader = pd.read_csv(path, chunksize=self.config.chunk_size)
        for chunk in reader:
            check_memory_limit(self.config.max_memory_mb, logger)
            yield chunk

    def _process_chunk(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            df = self._cleanse(df)
            df = self._validate(df)
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Chunk processing error: %s", exc)
        return df

    # ------------------------------------------------------------------
    # Stream processing
    # ------------------------------------------------------------------
    def consume_stream(self) -> Iterator[pd.DataFrame]:
        if not self._consumer:
            logger.warning("Kafka consumer not initialized")
            return iter(())
        while True:
            msg = self._consumer.poll(1.0)
            if msg is None:
                break
            if msg.error():  # pragma: no cover - runtime
                logger.error("Kafka error: %s", msg.error())
                continue
            try:
                payload = json.loads(msg.value())
                df = pd.DataFrame([payload])
                yield self._process_chunk(df)
                self._consumer.commit(asynchronous=True)
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Stream processing error: %s", exc)

    # ------------------------------------------------------------------
    # Validation / Cleansing
    # ------------------------------------------------------------------
    def _cleanse(self, df: pd.DataFrame) -> pd.DataFrame:
        # Unicode sanitization via existing helper
        from yosai_intel_dashboard.src.services.data_processing.file_processor import UnicodeFileProcessor as _UFP

        cleaned = _UFP.sanitize_dataframe_unicode(df, chunk_size=self.config.chunk_size)
        return (
            cleaned if isinstance(cleaned, pd.DataFrame) else pd.concat(list(cleaned))
        )

    def _validate(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            from validation.security_validator import SecurityValidator

            validator = SecurityValidator()
            return validator.file_validator.validate_dataframe(df)  # type: ignore[attr-defined]
        except Exception:
            return df

    # ------------------------------------------------------------------
    # ETL/ELT helpers
    # ------------------------------------------------------------------
    def extract(self, path: str) -> Iterable[pd.DataFrame]:
        return self._read_chunks(path)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._process_chunk(df)

    def load(self, df: pd.DataFrame, output: Callable[[pd.DataFrame], None]) -> None:
        try:
            output(df)
            self._record_lineage("load_success", rows=len(df))
        except Exception as exc:
            logger.error("Load failed: %s", exc)
            self._record_lineage("load_failed", error=str(exc))

    # ------------------------------------------------------------------
    # Parallel processing
    # ------------------------------------------------------------------
    def _process_parallel(self, dfs: List[pd.DataFrame]) -> List[pd.DataFrame]:
        if self.config.use_ray and ray:
            return ray.get([ray.remote(self._process_chunk).remote(df) for df in dfs])  # type: ignore
        if mp and self.config.num_workers > 1:
            with mp.Pool(self.config.num_workers) as pool:
                return pool.map(self._process_chunk, dfs)
        return [self._process_chunk(df) for df in dfs]

    # ------------------------------------------------------------------
    # Checkpointing
    # ------------------------------------------------------------------
    def _write_checkpoint(self, index: int) -> None:
        try:
            self.config.checkpoint_path.write_text(str(index))
        except Exception:  # pragma: no cover - best effort
            pass

    def resume_from_checkpoint(self, path: str) -> pd.DataFrame:
        start = 0
        if self.config.checkpoint_path.exists():
            try:
                start = int(self.config.checkpoint_path.read_text().strip()) + 1
            except Exception:  # pragma: no cover - parse error
                start = 0
        chunks = []
        for i, chunk in enumerate(self._read_chunks(path)):
            if i < start:
                continue
            processed = self._process_chunk(chunk)
            chunks.append(processed)
            self._write_checkpoint(i)
        df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        self._record_lineage("resume_complete", rows=len(df))
        return df

    # ------------------------------------------------------------------
    def close(self) -> None:
        if self._producer:
            try:
                self._producer.flush()
            except Exception:  # pragma: no cover
                pass
        if self._consumer:
            try:
                self._consumer.close()
            except Exception:  # pragma: no cover
                pass


__all__ = ["DataProcessor", "ProcessorConfig", "KafkaConfig", "LineageRecord"]
