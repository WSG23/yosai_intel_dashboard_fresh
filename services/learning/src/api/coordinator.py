from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

from mapping.core.interfaces import LearningInterface, StorageInterface
from services.learning.src.ml.fingerprint_service import FingerprintService

logger = logging.getLogger(__name__)


class LearningCoordinator(LearningInterface):
    """High level orchestrator using storage and fingerprint utilities."""

    def __init__(self, storage: StorageInterface) -> None:
        self.storage = storage
        self.fp = FingerprintService()
        self.learned_data: Dict[str, Any] = self.storage.load()

    # ------------------------------------------------------------------
    def save_complete_mapping(
        self,
        df: pd.DataFrame,
        filename: str,
        device_mappings: Dict[str, Any],
        column_mappings: Dict[str, str] | None = None,
    ) -> str:
        fingerprint = self.fp.generate(df, filename)
        mapping = {
            "filename": filename,
            "fingerprint": fingerprint,
            "saved_at": datetime.now().isoformat(),
            "device_mappings": device_mappings,
            "column_mappings": column_mappings or {},
            "file_stats": {
                "rows": len(df),
                "columns": list(df.columns),
                "device_count": self.fp.count_unique_devices(df),
            },
        }
        self.learned_data[fingerprint] = mapping
        self.storage.save(self.learned_data)
        logger.info("Saved mapping %s", fingerprint[:8])
        return fingerprint

    # ------------------------------------------------------------------
    def get_learned_mappings(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        fingerprint = self.fp.generate(df, filename)
        if fingerprint in self.learned_data:
            learned = self.learned_data[fingerprint]
            return {
                "device_mappings": learned.get("device_mappings", {}),
                "column_mappings": learned.get("column_mappings", {}),
                "match_type": "exact",
                "saved_at": learned.get("saved_at"),
                "confidence": 1.0,
            }
        similar = self.fp.find_similar(df, self.learned_data)
        if similar:
            return {
                "device_mappings": similar.get("device_mappings", {}),
                "column_mappings": similar.get("column_mappings", {}),
                "match_type": "similar",
                "confidence": similar.get("similarity_score", 0.0),
                "source_file": similar.get("filename"),
            }
        return {
            "device_mappings": {},
            "column_mappings": {},
            "match_type": "none",
            "confidence": 0.0,
        }

    # ------------------------------------------------------------------
    def apply_to_global_store(self, df: pd.DataFrame, filename: str) -> bool:
        try:
            from services.ai_mapping_store import ai_mapping_store
        except Exception:  # pragma: no cover - optional dependency
            return False
        learned = self.get_learned_mappings(df, filename)
        if learned["match_type"] != "none" and learned["device_mappings"]:
            ai_mapping_store.clear()
            ai_mapping_store.update(learned["device_mappings"])
            return True
        return False

    # ------------------------------------------------------------------
    def get_statistics(self) -> Dict[str, Any]:
        if not self.learned_data:
            return {"total_mappings": 0, "total_devices": 0, "files": []}
        total_devices = sum(
            d["file_stats"]["device_count"] for d in self.learned_data.values()
        )
        latest = max(d["saved_at"] for d in self.learned_data.values())
        return {
            "total_mappings": len(self.learned_data),
            "total_devices": total_devices,
            "latest_save": latest,
            "files": [
                {
                    "filename": d["filename"],
                    "fingerprint": d["fingerprint"][:8],
                    "device_count": d["file_stats"]["device_count"],
                    "saved_at": d["saved_at"],
                }
                for d in self.learned_data.values()
            ],
        }
