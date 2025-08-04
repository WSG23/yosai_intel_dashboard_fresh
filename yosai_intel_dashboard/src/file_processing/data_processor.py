from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.core.error_handling import (
    ErrorCategory,
    ErrorSeverity,
    with_error_handling,
)

from .format_detector import FormatDetector, UnsupportedFormatError
from .readers import ArchiveReader, CSVReader, ExcelReader, FWFReader, JSONReader


@dataclass
class DataProcessorConfig:
    """Configuration options for :class:`DataProcessor`."""

    default_tz: str = "UTC"
    person_id_pattern: str = r".+"
    badge_id_pattern: str = r".+"
    device_match_threshold: int = 80
    pipeline_stage: str = "normalized"
    schema_version: str = "1.0"


class DataProcessor:
    """Process input files using ``FormatDetector`` and apply transformations."""

    def __init__(
        self,
        readers: list | None = None,
        hint: dict | None = None,
        *,
        config: DataProcessorConfig | None = None,
        device_registry: dict[str, dict] | None = None,
    ) -> None:
        self.format_detector = FormatDetector(
            readers
            or [CSVReader(), JSONReader(), ExcelReader(), FWFReader(), ArchiveReader()]
        )
        self.hint = hint or {}
        self.config = config or DataProcessorConfig()
        self.device_registry: dict[str, dict] = device_registry or {}
        self.pipeline_metadata: dict[str, dict] = {}
        self.unified_callbacks = TrulyUnifiedCallbacks()
        import re

        self._person_id_re = re.compile(self.config.person_id_pattern)
        self._badge_id_re = re.compile(self.config.badge_id_pattern)
        # Cache expensive lookups
        self._device_lookup_cache: dict[str, dict] = {}
        self._person_id_cache: dict[str, bool] = {}
        self._badge_id_cache: dict[str, bool] = {}

    def _normalize_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse and normalize the 'timestamp' column to UTC ISO-8601, and derive
        'date', 'hour_of_day', and 'day_of_week' fields.
        """
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise", utc=False)
        df["timestamp"] = (
            df["timestamp"]
            .dt.tz_localize(self.config.default_tz, ambiguous="infer")
            .dt.tz_convert("UTC")
        )
        df["date"] = df["timestamp"].dt.date
        df["hour_of_day"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.day_name()
        return df

    def _standardize_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and standardize 'person_id' and 'badge_id' using regex from yosai_intel_dashboard.src.infrastructure.config.
        Flags invalid entries and sets them to None.
        """
        df = df.copy()
        person_series = df["person_id"].astype(str)
        badge_series = df["badge_id"].astype(str)

        # Cache regex results for unique values to avoid repeated matching
        for val in person_series.unique():
            if val not in self._person_id_cache:
                self._person_id_cache[val] = bool(self._person_id_re.fullmatch(val))
        for val in badge_series.unique():
            if val not in self._badge_id_cache:
                self._badge_id_cache[val] = bool(self._badge_id_re.fullmatch(val))

        df["person_id_valid"] = person_series.map(self._person_id_cache).fillna(False)
        df["badge_id_valid"] = badge_series.map(self._badge_id_cache).fillna(False)
        df.loc[~df["person_id_valid"], "person_id"] = None
        df.loc[~df["badge_id_valid"], "badge_id"] = None
        invalid_p = int((~df["person_id_valid"]).sum())
        invalid_b = int((~df["badge_id_valid"]).sum())
        if invalid_p or invalid_b:
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_WARNING,
                "id_standardization",
                {
                    "invalid_person_ids": invalid_p,
                    "invalid_badge_ids": invalid_b,
                },
            )
        return df

    def _enrich_devices(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map free-text 'device_name' or 'door_id' to a registry (self.device_registry)
        via exact then fuzzy matching. Enrich with building, zone, type, geo fields.
        """
        from rapidfuzz import process

        df = df.copy()
        registry = self.device_registry
        cache = self._device_lookup_cache

        def lookup(name: str) -> dict:
            if name in cache:
                return cache[name]
            if name in registry:
                cache[name] = registry[name]
                return cache[name]
            match, score, _ = process.extractOne(
                name, registry.keys(), score_cutoff=self.config.device_match_threshold
            )
            if match:
                cache[name] = registry[match]
            else:
                self.unified_callbacks.trigger(
                    CallbackEvent.SYSTEM_WARNING,
                    "device_enrichment",
                    {"warning": f"Unmatched device '{name}'", "value": name},
                )
                cache[name] = {}
            return cache[name]

        try:
            enriched = df["device_name"].apply(lookup).apply(pd.Series)
            return pd.concat([df, enriched], axis=1)
        except Exception as exc:  # pragma: no cover - log and continue
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_ERROR,
                "device_enrichment",
                {"error": str(exc)},
            )
            return df

    def _enum_access_result(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map free-text 'access_result' to integer codes: GRANTED=1, DENIED=0, etc.
        """
        df = df.copy()
        mapping = {
            "access granted": 1,
            "granted": 1,
            "access denied": 0,
            "denied": 0,
        }

        normalized = (
            df["access_result"].astype(str).str.strip().str.lower().str.rstrip(".")
        )
        df["access_result_code"] = normalized.map(mapping)
        unknown = df[df["access_result_code"].isna()]["access_result"].unique()
        for val in unknown:
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_WARNING,
                "access_result_enum",
                {"warning": f"Unknown access_result '{val}'", "value": val},
            )
        return df

    def _hash_event_fingerprint(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate SHA-256 fingerprint of timestamp+person_id+door_id for de-dup & joins.
        """
        import hashlib

        df = df.copy()

        combined = (
            df["timestamp"].astype(str)
            + "_"
            + df["person_id"].astype(str)
            + "_"
            + df["door_id"].astype(str)
        )
        df["event_fingerprint"] = combined.map(
            lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
        )
        return df

    def _infer_boolean_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Auto-fill missing is_entry/is_exit based on 'device_name' keywords.
        """
        df = df.copy()
        lower_names = df["device_name"].astype(str).str.lower()
        df.loc[
            df["is_entry"].isna() & lower_names.str.contains("entrance"), "is_entry"
        ] = True
        df.loc[df["is_exit"].isna() & lower_names.str.contains("exit"), "is_exit"] = (
            True
        )
        return df

    def _schema_validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate DataFrame against a Pandera schema (core/schemas.py),
        log all violations as warnings, then return df unchanged.
        """
        from yosai_intel_dashboard.src.core.schemas import AccessLogSchema

        try:
            AccessLogSchema.validate(df, lazy=True)
        except Exception as e:  # pragma: no cover - best effort logging
            for err in getattr(e, "failure_cases", []):
                self.unified_callbacks.trigger(
                    CallbackEvent.SYSTEM_WARNING,
                    "schema_validation",
                    {
                        "warning": "Schema violation",
                        "check": err.get("check"),
                        "row": err.get("index"),
                    },
                )
        return df

    def _tag_lineage(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add 'pipeline_stage' and 'schema_version' for provenance.
        """
        df = df.copy()
        df["pipeline_stage"] = self.config.pipeline_stage or "normalized"
        df["schema_version"] = self.config.schema_version
        return df

    def load_file(self, file_path: str) -> pd.DataFrame:
        try:
            df_raw, meta = self.format_detector.detect_and_load(
                file_path, hint=self.hint
            )
            self.pipeline_metadata["last_ingest"] = meta
            return df_raw
        except UnsupportedFormatError as exc:
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_ERROR,
                file_path,
                {"error": str(exc)},
            )
            raise

    @with_error_handling(
        category=ErrorCategory.FILE_PROCESSING,
        severity=ErrorSeverity.MEDIUM,
    )
    def _apply_timestamp_normalization(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize timestamps with unified error handling."""
        return self._normalize_timestamps(df)

    @with_error_handling(
        category=ErrorCategory.FILE_PROCESSING,
        severity=ErrorSeverity.MEDIUM,
    )
    def _apply_id_standardization(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize IDs with unified error handling."""
        return self._standardize_ids(df)

    @with_error_handling(
        category=ErrorCategory.FILE_PROCESSING,
        severity=ErrorSeverity.MEDIUM,
    )
    def _apply_device_enrichment(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich device information with unified error handling."""
        return self._enrich_devices(df)

    # Main processing pipeline
    def process(self, file_path: str) -> pd.DataFrame:
        df = self.load_file(file_path)

        result = self._apply_timestamp_normalization(df)
        if result is not None:
            df = result
        result = self._apply_id_standardization(df)
        if result is not None:
            df = result
        result = self._apply_device_enrichment(df)
        if result is not None:
            df = result

        df = self._enum_access_result(df)
        df = self._hash_event_fingerprint(df)
        df = self._infer_boolean_flags(df)
        df = self._schema_validate(df)
        df = self._tag_lineage(df)

        return df
