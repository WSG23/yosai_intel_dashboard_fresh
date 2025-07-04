"""Export helpers for enhanced learning data."""
import json
from typing import Dict, Any, List
import pandas as pd
from services.consolidated_learning_service import get_learning_service
from services.device_learning_service import get_device_learning_service


def get_enhanced_data() -> Dict[str, Any]:
    """Return enhanced mapping data consolidating all current sources."""
    # Consolidate from multiple sources since learned_data might be empty
    enhanced_data = {}

    # Get from consolidated learning service
    learning_service = get_learning_service()
    if learning_service.learned_data:
        enhanced_data.update(learning_service.learned_data)

    # Get from device learning service as fallback/supplement
    device_service = get_device_learning_service()
    if hasattr(device_service, 'learned_mappings') and device_service.learned_mappings:
        # Convert device mappings to consolidated format
        for device_id, mapping in device_service.learned_mappings.items():
            fingerprint = f"device_{device_id}"
            enhanced_data[fingerprint] = {
                "fingerprint": fingerprint,
                "filename": f"{device_id}_mappings.csv",
                "saved_at": mapping.get("saved_at", ""),
                "source": "device_learning",
                "device_count": 1,
                "device_mappings": {device_id: mapping},
                "column_mappings": {}
            }

    # Try to get from global AI mapping store as additional source
    try:
        from services.ai_mapping_store import ai_mapping_store
        if hasattr(ai_mapping_store, 'all') and ai_mapping_store.all():
            ai_mappings = ai_mapping_store.all()
            for device_id, mapping in ai_mappings.items():
                fingerprint = f"ai_{device_id}"
                enhanced_data[fingerprint] = {
                    "fingerprint": fingerprint,
                    "filename": f"ai_{device_id}_mappings.csv",
                    "saved_at": mapping.get("saved_at", ""),
                    "source": "ai_mapping_store",
                    "device_count": 1,
                    "device_mappings": {device_id: mapping},
                    "column_mappings": {}
                }
    except ImportError:
        pass

    return enhanced_data


def get_device_learning_data() -> Dict[str, Any]:
    """Return raw device learning mappings."""
    service = get_device_learning_service()
    return getattr(service, 'learned_mappings', {})


def to_json_string(data: Dict[str, Any]) -> str:
    """Serialize enhanced data to pretty JSON string with UTF-8 safety."""
    def sanitize_for_json(obj):
        """Recursively sanitize unicode surrogate characters."""
        if isinstance(obj, str):
            # Replace unicode surrogates that can't be encoded in UTF-8
            return obj.encode('utf-8', errors='replace').decode('utf-8')
        elif isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_for_json(item) for item in obj]
        return obj

    sanitized_data = sanitize_for_json(data)
    return json.dumps(sanitized_data, indent=2, ensure_ascii=False)


def to_csv_string(data: Dict[str, Any]) -> str:
    """Serialize enhanced data to CSV string matching your wide format structure."""
    if not data:
        return ""

    # Create records matching your CSV structure with mappings.* and device_mappings.* columns
    records = []

    for fingerprint, content in data.items():
        # Base record structure
        record = {
            "fingerprint": fingerprint,
            "filename": content.get("filename", ""),
            "saved_at": content.get("saved_at", ""),
            "source": content.get("source", "user_confirmed"),
            "device_count": content.get("device_count", 0)
        }

        # Add flattened device mappings in both mappings.* and device_mappings.* format
        device_mappings = content.get("device_mappings", {})
        for device_id, device_data in device_mappings.items():
            if isinstance(device_data, dict):
                # Create mappings.{device_id}.{property} columns
                for prop, value in device_data.items():
                    mappings_key = f"mappings.{device_id}.{prop}"
                    device_mappings_key = f"device_mappings.{device_id}.{prop}"
                    record[mappings_key] = _sanitize_csv_value(value)
                    record[device_mappings_key] = _sanitize_csv_value(value)

        # Add column mappings if present
        column_mappings = content.get("column_mappings", {})
        for col_name, mapped_name in column_mappings.items():
            record[f"column_mappings.{col_name}"] = _sanitize_csv_value(mapped_name)

        records.append(record)

    if not records:
        return ""

    # Create DataFrame and ensure consistent column ordering
    df = pd.DataFrame(records)

    # Sort columns to match your expected format: base columns first, then mappings
    base_cols = ["fingerprint", "filename", "saved_at", "source", "device_count"]
    mapping_cols = [col for col in df.columns if col.startswith(("mappings.", "device_mappings.", "column_mappings."))]
    ordered_cols = base_cols + sorted(mapping_cols)

    # Reorder columns, keeping only those that exist
    existing_cols = [col for col in ordered_cols if col in df.columns]
    df = df[existing_cols]

    return df.to_csv(index=False)


def _sanitize_csv_value(value) -> str:
    """Sanitize individual CSV values for UTF-8 safety."""
    if value is None:
        return ""

    # Convert to string and handle unicode surrogates
    str_value = str(value)
    try:
        # Test if it can be properly encoded
        str_value.encode('utf-8')
        return str_value
    except UnicodeEncodeError:
        # Replace problematic characters
        return str_value.encode('utf-8', errors='replace').decode('utf-8')


# Consolidate current data when module loads to ensure exports have content

def _bootstrap_enhanced_data():
    """Bootstrap enhanced data by consolidating from all available sources."""
    try:
        learning_service = get_learning_service()
        if not learning_service.learned_data:
            # Try to populate from device learning service
            device_data = get_device_learning_data()
            if device_data:
                # Convert and save device data to learning service
                from datetime import datetime
                enhanced_entry = {
                    "filename": "consolidated_device_data.csv",
                    "saved_at": datetime.now().isoformat(),
                    "source": "bootstrap",
                    "device_count": len(device_data),
                    "device_mappings": device_data,
                    "column_mappings": {}
                }
                fingerprint = f"bootstrap_{len(device_data)}"
                learning_service.learned_data[fingerprint] = enhanced_entry
                learning_service._persist_learned_data()
    except Exception as e:
        # Silently handle bootstrap errors
        pass


# Bootstrap on import
_bootstrap_enhanced_data()


__all__ = [
    "get_enhanced_data",
    "get_device_learning_data",
    "to_json_string",
    "to_csv_string",
]
