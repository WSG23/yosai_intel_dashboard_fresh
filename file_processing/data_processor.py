from __future__ import annotations
from core.truly_unified_callbacks import TrulyUnifiedCallbacks

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from core.unified_callbacks import CallbackEvent
from analytics_core.callbacks.unified_callback_manager import CallbackManager
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
        readers: Optional[list] = None,
        hint: Optional[Dict] = None,
        *,
        config: Optional[DataProcessorConfig] = None,
        device_registry: Optional[Dict[str, Dict]] = None,
    ) -> None:
        self.format_detector = FormatDetector(
            readers or [CSVReader(), JSONReader(), ExcelReader(), FWFReader(), ArchiveReader()]
        )
        self.hint = hint or {}
        self.config = config or DataProcessorConfig()
        self.device_registry: Dict[str, Dict] = device_registry or {}
        self.pipeline_metadata: Dict[str, Dict] = {}
        self.unified_callbacks = CallbackManager()

    def _normalize_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse and normalize the 'timestamp' column to UTC ISO-8601, and derive
        'date', 'hour_of_day', and 'day_of_week' fields.
        """
        df = df.copy()
        df["timestamp"] = pd.to_datetime(
            df["timestamp"], errors="raise", utc=False
        )
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
        Validate and standardize 'person_id' and 'badge_id' using regex from config.
        Flags invalid entries and sets them to None.
        """
        import re

        df = df.copy()
        pid_re = re.compile(self.config.person_id_pattern)
        bid_re = re.compile(self.config.badge_id_pattern)
        df["person_id_valid"] = df["person_id"].astype(str).apply(
            lambda x: bool(pid_re.fullmatch(x))
        )
        df["badge_id_valid"] = df["badge_id"].astype(str).apply(
            lambda x: bool(bid_re.fullmatch(x))
        )
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

        def lookup(name: str) -> Dict:
            if name in registry:
                return registry[name]
            match, score, _ = process.extractOne(
                name, registry.keys(), score_cutoff=self.config.device_match_threshold
            )
            if match:
                return registry[match]
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_WARNING,
                "device_enrichment",
                {"warning": f"Unmatched device '{name}'", "value": name},
            )
            return {}

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

        def to_code(val: object) -> Optional[int]:
            key = str(val).strip().lower().rstrip(".")
            code = mapping.get(key)
            if code is None:
                self.unified_callbacks.trigger(
                    CallbackEvent.SYSTEM_WARNING,
                    "access_result_enum",
                    {"warning": f"Unknown access_result '{val}'", "value": val},
                )
            return code

        df["access_result_code"] = df["access_result"].apply(to_code)
        return df

    def _hash_event_fingerprint(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate SHA-256 fingerprint of timestamp+person_id+door_id for de-dup & joins.
        """
        import hashlib

        df = df.copy()

        def make_hash(row: pd.Series) -> str:
            s = f"{row['timestamp']}_{row['person_id']}_{row['door_id']}"
            return hashlib.sha256(s.encode("utf-8")).hexdigest()

        df["event_fingerprint"] = df.apply(make_hash, axis=1)
        return df

    def _infer_boolean_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Auto-fill missing is_entry/is_exit based on 'device_name' keywords.
        """
        df = df.copy()
        df["is_entry"] = df.apply(
            lambda r: True
            if pd.isna(r.get("is_entry")) and "entrance" in str(r["device_name"]).lower()
            else r.get("is_entry"),
            axis=1,
        )
        df["is_exit"] = df.apply(
            lambda r: True
            if pd.isna(r.get("is_exit")) and "exit" in str(r["device_name"]).lower()
            else r.get("is_exit"),
            axis=1,
        )
        return df

    def _schema_validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate DataFrame against a Pandera schema (core/schemas.py),
        log all violations as warnings, then return df unchanged.
        """
        from core.schemas import AccessLogSchema

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
            df_raw, meta = self.format_detector.detect_and_load(file_path, hint=self.hint)
            self.pipeline_metadata["last_ingest"] = meta
            return df_raw
        except UnsupportedFormatError as exc:
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_ERROR,
                file_path,
                {"error": str(exc)},
            )
            raise

    # Main processing pipeline
    def process(self, file_path: str) -> pd.DataFrame:
        df = self.load_file(file_path)

        try:
            df = self._normalize_timestamps(df)
        except Exception as exc:  # pragma: no cover - log and continue
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_WARNING,
                "timestamp_normalization",
                {"error": str(exc)},
            )

        try:
            df = self._standardize_ids(df)
        except Exception as exc:  # pragma: no cover - log and continue
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_WARNING,
                "id_standardization",
                {"error": str(exc)},
            )

        try:
            df = self._enrich_devices(df)
        except Exception as exc:  # pragma: no cover - log and continue
            self.unified_callbacks.trigger(
                CallbackEvent.SYSTEM_ERROR,
                "device_enrichment",
                {"error": str(exc)},
            )

        df = self._enum_access_result(df)
        df = self._hash_event_fingerprint(df)
        df = self._infer_boolean_flags(df)
        df = self._schema_validate(df)
        df = self._tag_lineage(df)

        return df

