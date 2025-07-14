from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from .unicode_fix_module import sanitize_dataframe

try:
    from services.device_learning_service import DeviceLearningService
except Exception:  # pragma: no cover - fallback if service missing
    DeviceLearningService = None


class DataVerificationComponent:
    """Simple CLI-based data verification before enhancement."""

    def __init__(self) -> None:
        self.learning_service = DeviceLearningService() if DeviceLearningService else None

    def verify_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Interactively confirm column mapping and device classification."""
        df = sanitize_dataframe(df)
        print("\nDetected columns:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        mapping: Dict[str, str] = {}
        device_col = None
        if self.learning_service:
            device_col = self.learning_service._find_device_column(df)  # type: ignore[attr-defined]
        if device_col:
            print(f"\nSuggested device column: {device_col}")
        inp = input("Enter device column name (or press Enter to accept suggestion): ")
        if inp:
            device_col = inp
        if device_col and device_col in df.columns:
            mapping["device_column"] = device_col
        print("\nSample rows:")
        print(df.head().to_string(index=False))
        return df, mapping

    def save_verification(self, mapping: Dict[str, str], out_path: Path) -> None:
        data = {"mapping": mapping}
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
