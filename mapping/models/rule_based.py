from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml

DATA_DIR = Path(__file__).resolve().parent / "data"


@dataclass
class ColumnRules:
    english: Dict[str, List[str]]
    japanese: Dict[str, List[str]]


def load_rules(data_dir: Path = DATA_DIR) -> ColumnRules:
    """Load column mapping rules from YAML files."""
    with open(data_dir / "english_columns.yaml", "r", encoding="utf-8") as f:
        english = yaml.safe_load(f) or {}
    with open(data_dir / "japanese_columns.yaml", "r", encoding="utf-8") as f:
        japanese = yaml.safe_load(f) or {}
    return ColumnRules(english=english, japanese=japanese)
