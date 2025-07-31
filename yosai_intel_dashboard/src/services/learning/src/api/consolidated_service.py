"""
Consolidated learning service for device and column mappings.
Replaces services/device_learning_service.py
"""

import asyncio
import hashlib
import json
import logging
from unicode_toolkit import safe_encode_text
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from core.cache_manager import CacheConfig, InMemoryCacheManager

_cache_manager = InMemoryCacheManager(CacheConfig())


class ConsolidatedLearningService:
    """Unified learning service for all mapping types."""

    def __init__(self, storage_path: str = "data/learned_mappings.json"):
        self.storage_path = Path(storage_path)
        self.learned_data: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_learned_data()

    def save_complete_mapping(
        self,
        df: pd.DataFrame,
        filename: str,
        device_mappings: Dict[str, Any],
        column_mappings: Optional[Dict[str, str]] = None,
    ) -> str:
        """Save device and column mappings for future use."""
        fingerprint = self._generate_fingerprint(df, filename)

        mapping_data = {
            "filename": filename,
            "fingerprint": fingerprint,
            "saved_at": datetime.now().isoformat(),
            "device_mappings": device_mappings,
            "column_mappings": column_mappings or {},
            "file_stats": {
                "rows": len(df),
                "columns": list(df.columns),
                "device_count": self._count_unique_devices(df),
            },
        }

        self.learned_data[fingerprint] = mapping_data
        self._persist_learned_data()
        try:
            asyncio.run(_cache_manager.clear())
        except Exception:
            pass
        self.logger.info(
            "Saved mapping %s for %s",
            fingerprint[:8],
            safe_encode_text(filename),
        )
        return fingerprint

    def get_learned_mappings(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Retrieve learned mappings for similar data."""
        fingerprint = self._generate_fingerprint(df, filename)

        if fingerprint in self.learned_data:
            learned = self.learned_data[fingerprint]
            self.logger.info(
                "Found exact match for %s",
                safe_encode_text(filename),
            )
            return {
                "device_mappings": learned["device_mappings"],
                "column_mappings": learned["column_mappings"],
                "match_type": "exact",
                "saved_at": learned["saved_at"],
                "confidence": 1.0,
            }

        similar = self._find_similar_mapping(df)
        if similar:
            self.logger.info(
                "Found similar mapping for %s",
                safe_encode_text(filename),
            )
            return {
                "device_mappings": similar["device_mappings"],
                "column_mappings": similar["column_mappings"],
                "match_type": "similar",
                "confidence": similar["similarity_score"],
                "source_file": similar["filename"],
            }

        return {
            "device_mappings": {},
            "column_mappings": {},
            "match_type": "none",
            "confidence": 0.0,
        }

    def apply_to_global_store(self, df: pd.DataFrame, filename: str) -> bool:
        """Apply learned mappings to global device mapping store."""
        try:
            from yosai_intel_dashboard.src.services.ai_mapping_store import ai_mapping_store
        except ImportError:
            self.logger.warning("Could not import global device mappings store")
            return False

        learned = self.get_learned_mappings(df, filename)
        if learned["match_type"] != "none" and learned["device_mappings"]:
            ai_mapping_store.clear()
            ai_mapping_store.update(learned["device_mappings"])
            self.logger.info(
                f"Applied {len(learned['device_mappings'])} learned device mappings"
            )
            return True
        return False

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics."""
        if not self.learned_data:
            return {"total_mappings": 0, "total_devices": 0, "files": []}

        total_devices = sum(
            data["file_stats"]["device_count"] for data in self.learned_data.values()
        )

        latest_save = (
            max(data["saved_at"] for data in self.learned_data.values())
            if self.learned_data
            else None
        )

        return {
            "total_mappings": len(self.learned_data),
            "total_devices": total_devices,
            "latest_save": latest_save,
            "files": [
                {
                    "filename": data["filename"],
                    "fingerprint": data["fingerprint"][:8],
                    "device_count": data["file_stats"]["device_count"],
                    "saved_at": data["saved_at"],
                }
                for data in self.learned_data.values()
            ],
        }

    def _generate_fingerprint(self, df: pd.DataFrame, filename: str) -> str:
        """Generate unique fingerprint for data structure."""
        structure = {
            "filename": filename,
            "columns": sorted(df.columns.tolist()),
            "row_count": len(df),
            "column_count": len(df.columns),
        }
        content = json.dumps(structure, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def _find_similar_mapping(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Find similar mapping based on column structure."""
        current_columns = set(df.columns)
        best_match = None
        best_score = 0.0
        similarity_threshold = 0.7

        for data in self.learned_data.values():
            stored_columns = set(data["file_stats"]["columns"])
            intersection = len(current_columns & stored_columns)
            union = len(current_columns | stored_columns)
            similarity = intersection / union if union > 0 else 0.0
            if similarity > best_score and similarity >= similarity_threshold:
                best_score = similarity
                best_match = data.copy()
                best_match["similarity_score"] = similarity
        return best_match

    def _count_unique_devices(self, df: pd.DataFrame) -> int:
        """Count unique devices in dataframe."""
        if df.empty:
            return 0
        device_columns = ["door_id", "device_id", "device_name", "device"]
        for col in device_columns:
            if col in df.columns:
                return df[col].nunique()
        return df.iloc[:, 0].nunique() if len(df.columns) > 0 else 0

    def _load_learned_data(self):
        """Load learned data from storage using JSON only."""
        if self.storage_path.exists():
            try:
                with open(
                    self.storage_path, "r", encoding="utf-8", errors="replace"
                ) as f:
                    self.learned_data = json.load(f)
                self.logger.info(f"Loaded {len(self.learned_data)} learned mappings")
            except Exception as e:
                self.logger.warning(f"Could not load learned data: {e}")
                self.learned_data = {}
        else:
            self.learned_data = {}

    def _persist_learned_data(self):
        """Persist learned data to storage using JSON."""
        try:
            with open(self.storage_path, "w", encoding="utf-8", errors="replace") as f:
                json.dump(self.learned_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not persist learned data: {e}")


_learning_service: Optional[ConsolidatedLearningService] = None


def get_learning_service() -> ConsolidatedLearningService:
    """Get global learning service instance."""
    global _learning_service
    if _learning_service is None:
        _learning_service = ConsolidatedLearningService()
    return _learning_service
