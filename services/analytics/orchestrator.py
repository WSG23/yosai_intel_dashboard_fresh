from __future__ import annotations

"""High level orchestration for analytics workflows."""

from typing import Any, Dict, Protocol
import logging
import pandas as pd

from validation.security_validator import SecurityValidator

from .data_loader import DataLoader
from .protocols import DataProcessorProtocol
from .publisher import Publisher

logger = logging.getLogger(__name__)


class AnalyticsRepositoryProtocol(Protocol):
    """Minimal repository used by :class:`AnalyticsOrchestrator`."""

    def save_summary(self, summary: Dict[str, Any]) -> None:  # pragma: no cover - interface
        ...


class AnalyticsOrchestrator:
    """Coordinate loader, validator, processor and persistence."""

    def __init__(
        self,
        loader: DataLoader,
        validator: SecurityValidator,
        processor: DataProcessorProtocol,
        repository: AnalyticsRepositoryProtocol | None,
        publisher: Publisher,
    ) -> None:
        self.loader = loader
        self.validator = validator
        self.processor = processor

        self.repository = repository
        self.publisher = publisher

    # ------------------------------------------------------------------
    def process_uploaded_data(self) -> Dict[str, Any]:
        """Load, validate, process and summarize uploaded data."""
        try:
            uploaded = self.loader.load_uploaded_data()
            if not uploaded:
                result = {"status": "no_data", "message": "No uploaded files available"}
                self.publisher.publish(result)
                return result

            frames: list[pd.DataFrame] = []
            for name, df in uploaded.items():
                try:
                    csv_bytes = df.to_csv(index=False).encode("utf-8")
                    self.validator.validate_file_upload(name, csv_bytes)
                except Exception as exc:  # pragma: no cover - validation failures
                    logger.error("Validation failed for %s: %s", name, exc)
                    continue
                cleaned = self.loader.clean_uploaded_dataframe(df)
                processed = self.processor.process_access_events(cleaned)
                frames.append(processed)

            if not frames:
                result = {"status": "no_data", "message": "No valid uploaded data"}
                self.publisher.publish(result)
                return result

            combined = frames[0] if len(frames) == 1 else pd.concat(frames, ignore_index=True)
            summary = self.loader.summarize_dataframe(combined)

            if self.repository is not None:
                try:
                    self.repository.save_summary(summary)
                except Exception as exc:  # pragma: no cover - best effort
                    logger.debug("Repository save failed: %s", exc)

            self.publisher.publish(summary)
            return summary
        except Exception as exc:  # pragma: no cover - best effort
            logger.exception("Processing uploaded data failed: %s", exc)
            result = {"status": "error", "message": str(exc)}
            self.publisher.publish(result)
            return result


__all__ = ["AnalyticsOrchestrator", "AnalyticsRepositoryProtocol"]

