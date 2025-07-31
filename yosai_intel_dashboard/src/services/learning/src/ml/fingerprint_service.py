from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

import pandas as pd


class FingerprintService:
    """Utility for generating fingerprints and similarity checks."""

    def generate(self, df: pd.DataFrame, filename: str) -> str:
        structure = {
            "filename": filename,
            "columns": sorted(df.columns.tolist()),
            "row_count": len(df),
            "column_count": len(df.columns),
        }
        content = json.dumps(structure, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def count_unique_devices(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        for col in ("door_id", "device_id", "device_name", "device"):
            if col in df.columns:
                return df[col].nunique()
        return df.iloc[:, 0].nunique() if len(df.columns) > 0 else 0

    def find_similar(
        self, df: pd.DataFrame, learned: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        current = set(df.columns)
        best: Optional[Dict[str, Any]] = None
        best_score = 0.0
        for data in learned.values():
            stored = set(data.get("file_stats", {}).get("columns", []))
            inter = len(current & stored)
            union = len(current | stored)
            score = inter / union if union else 0.0
            if score > best_score and score >= 0.7:
                best_score = score
                best = dict(data)
                best["similarity_score"] = score
        return best
