"""Export helpers for enhanced learning data."""


import json
from typing import Dict, Any
import pandas as pd

from services.consolidated_learning_service import get_learning_service


def get_enhanced_data() -> Dict[str, Any]:
    """Return enhanced mapping data from the learning service."""
    service = get_learning_service()
    return service.learned_data


def to_json_string(data: Dict[str, Any]) -> str:
    """Serialize enhanced data to pretty JSON string."""
    return json.dumps(data, indent=2, ensure_ascii=False)


def to_csv_string(data: Dict[str, Any]) -> str:
    """Serialize enhanced data to CSV string using flattened structure."""
    if not data:
        return ""
    records = []
    for fingerprint, content in data.items():
        record = {"fingerprint": fingerprint}
        record.update(content)
        records.append(record)
    df = pd.json_normalize(records)
    return df.to_csv(index=False)


__all__ = ["get_enhanced_data", "to_json_string", "to_csv_string"]
