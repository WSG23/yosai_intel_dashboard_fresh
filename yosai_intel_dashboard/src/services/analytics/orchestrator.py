from __future__ import annotations

"""High level orchestration for analytics workflows."""

import logging
from typing import Any, Dict, Protocol

import pandas as pd
from validation.security_validator import SecurityValidator

from shared.events import publish_event
from yosai_intel_dashboard.src.utils.text_utils import safe_text

from .data.loader import DataLoader
from .protocols import DataProcessorProtocol

logger = logging.getLogger(__name__)


class AnalyticsRepositoryProtocol(Protocol):
    """Minimal repository used by :class:`AnalyticsOrchestrator`."""

    def save_summary(
        self, summary: Dict[str, Any]
    ) -> None:  # pragma: no cover - interface
        ...


class AnalyticsOrchestrator:
    """Coordinate loader, validator, processor and persistence."""

    def __init__(
        self,
        loader: DataLoader,
        validator: SecurityValidator,
        processor: DataProcessorProtocol,
        repository: AnalyticsRepositoryProtocol | None,
        event_bus: Any | None,
    ) -> None:
        self.loader = loader
        self.validator = validator
        self.processor = processor

        self.repository = repository
        self.event_bus = event_bus

    # ------------------------------------------------------------------
    def process_uploaded_data(self) -> Dict[str, Any]:
        """Load, validate, process and summarize uploaded data."""
        try:
            uploaded = self.loader.load_uploaded_data()
            if not uploaded:
                result = {"status": "no_data", "message": "No uploaded files available"}
                publish_event(self.event_bus, result)
                return result

            frames: list[pd.DataFrame] = []
            for name, df in uploaded.items():
                try:
                    csv_bytes = df.to_csv(index=False).encode("utf-8")
                    self.validator.validate_file_upload(name, csv_bytes)
                except Exception as exc:  # pragma: no cover - validation failures
                    logger.error("Validation failed for %s: %s", name, safe_text(exc))
                    continue
                cleaned = self.loader.clean_uploaded_dataframe(df)
                processed = self.processor.process_access_events(cleaned)
                frames.append(processed)

            if not frames:
                result = {"status": "no_data", "message": "No valid uploaded data"}
                publish_event(self.event_bus, result)
                return result

            combined = (
                frames[0] if len(frames) == 1 else pd.concat(frames, ignore_index=True)
            )
            summary = self.loader.summarize_dataframe(combined)

            if self.repository is not None:
                try:
                    self.repository.save_summary(summary)
                except Exception as exc:  # pragma: no cover - best effort
                    logger.debug("Repository save failed: %s", safe_text(exc))

            publish_event(self.event_bus, summary)
            return summary
        except Exception as exc:  # pragma: no cover - best effort
            logger.exception(
                "Processing uploaded data failed: %s", safe_text(exc)
            )
            result = {
                "status": "error",
                "message": safe_text(exc),
                "error_code": "PROCESSING_FAILED",
            }
            publish_event(self.event_bus, result)
            return result


__all__ = ["AnalyticsOrchestrator", "AnalyticsRepositoryProtocol"]
