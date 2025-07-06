"""Export helpers for enhanced learning data."""
import json
import re
from datetime import datetime
from typing import Any, Dict, List

from core.serialization import SafeJSONSerializer

# JSON sanitizer used for export formatting
_serializer = SafeJSONSerializer()

import pandas as pd

from services.consolidated_learning_service import get_learning_service
from services.device_learning_service import get_device_learning_service


def get_enhanced_data() -> Dict[str, Any]:
    """Return enhanced mapping data consolidating all current sources."""
    enhanced: Dict[str, Any] = {}

    # 1) from consolidated learning service
    svc = get_learning_service()
    if svc.learned_data:
        for fp, content in svc.learned_data.items():
            if isinstance(content, dict) and content.get("filename"):
                enhanced[fp] = content

    # 2) from device learning service
    dev_svc = get_device_learning_service()
    if hasattr(dev_svc, "learned_mappings") and dev_svc.learned_mappings:
        dm = dev_svc.learned_mappings
        fp = "device_learning_consolidated"
        enhanced[fp] = {
            "fingerprint":    fp,
            "filename":       "device_learning_mappings.csv",
            "saved_at":       datetime.now().isoformat(),
            "source":         "device_learning",
            "device_count":   len(dm),
            "device_mappings": dm,
            "column_mappings": {}
        }

    # 3) from global AI mapping store
    try:
        from services.ai_mapping_store import ai_mapping_store  # noqa: E402
        if hasattr(ai_mapping_store, "all") and ai_mapping_store.all():
            ai_map = ai_mapping_store.all()
            fp = "ai_mapping_store_consolidated"
            enhanced[fp] = {
                "fingerprint":    fp,
                "filename":       "ai_mappings.csv",
                "saved_at":       datetime.now().isoformat(),
                "source":         "ai_mapping_store",
                "device_count":   len(ai_map),
                "device_mappings": ai_map,
                "column_mappings": {}
            }
    except ImportError:
        pass

    return enhanced


def get_device_learning_data() -> Dict[str, Any]:
    """Return raw device learning mappings."""
    svc = get_device_learning_service()
    return getattr(svc, "learned_mappings", {})


def to_json_string(data: Dict[str, Any]) -> str:
    """Serialize enhanced data to pretty JSON string with UTF-8 safety."""
    clean = _serializer.serialize(data)
    # keep only real devices in JSON exports
    for fp, content in clean.items():
        raw = content.get("device_mappings", {})
        content["device_mappings"] = _extract_only_devices(raw)

    # Ensure normalization happens before JSON encoding
    sanitized = _serializer.serialize(clean)
    return json.dumps(sanitized, indent=2, ensure_ascii=False)


def to_csv_string(data: Dict[str, Any]) -> str:
    """
    Serialize enhanced data to CSV in *long* form:
      • one row per device mapping
      • columns: fingerprint, filename, saved_at, source, device_count,
                 (any column_mappings.*), device_id, <device_props...>
    """
    if not data:
        return ""

    rows: List[Dict[str, Any]] = []
    for fp, content in data.items():
        # base columns
        base = {
            "fingerprint":  fp,
            "filename":     content.get("filename", ""),
            "saved_at":     content.get("saved_at", ""),
            "source":       content.get("source", "user_confirmed"),
            "device_count": content.get("device_count", 0),
        }

        # include any column_mappings.*
        for col, mapped in content.get("column_mappings", {}).items():
            base[f"column_mapping.{col}"] = _sanitize_csv_value(mapped)

        # extract only the real devices
        raw = content.get("device_mappings", {})
        devices = _extract_only_devices(raw)

        # emit one row per device
        for device_id, device_val in devices.items():
            row = dict(base)
            row["device_id"] = device_id

            # parse each device’s props
            if isinstance(device_val, dict):
                props = _parse_ai_extraction(device_val)
            else:
                props = _parse_bundled_extraction_string(device_val)

            for prop, val in props.items():
                row[prop] = _sanitize_csv_value(val)

            rows.append(row)

    if not rows:
        return ""

    df = pd.DataFrame(rows)

    # determine column order
    fixed = ["fingerprint", "filename", "saved_at", "source", "device_count"]
    # any of the column_mapping.* columns
    cm = sorted(c for c in df.columns if c.startswith("column_mapping."))
    # the device identifier
    mid = ["device_id"]
    # all remaining device-prop columns
    others = [c for c in df.columns if c not in fixed + cm + mid]
    ordered = fixed + cm + mid + sorted(others)

    df = df.loc[:, ordered]
    return df.to_csv(index=False)


def _extract_only_devices(m: Any) -> Dict[str, Any]:
    """
    Dive into a nested mapping and return only those entries where:
      • key is NOT a hex-fingerprint, AND
      • val is either
          – a dict with one of the device-properties, OR
          – a bundled string (floor/security/entry/exit…),
        and unwrap any file-wrapper dicts that have
        {filename, saved_at, device_count, device_mappings}.
    """
    out: Dict[str, Any] = {}
    if not isinstance(m, dict):
        return out

    for key, val in m.items():
        # skip raw-fingerprint keys
        if isinstance(key, str) and _is_fingerprint(key):
            continue

        # unwrap any file-wrapper dict
        if (
            isinstance(val, dict)
            and {"filename", "saved_at", "device_count", "device_mappings"}.issubset(val.keys())
        ):
            inner = val["device_mappings"]
            out.update(_extract_only_devices(inner))
            continue

        # if this dict *is* a device, keep it
        if isinstance(val, dict) and _has_device_properties(val):
            out[key] = val
            continue

        # otherwise recurse deeper
        if isinstance(val, dict):
            out.update(_extract_only_devices(val))
            continue

        # or if this is a bundled-string
        if isinstance(val, str) and any(tok in val.lower() for tok in ("floor","security","entry","exit")):
            out[key] = val
            continue

    return out


def _is_fingerprint(k: str) -> bool:
    if not isinstance(k, str):
        return False
    if len(k) < 8 or len(k) > 32:
        return False
    try:
        int(k, 16)
        return True
    except ValueError:
        return False


def _has_device_properties(d: Dict[str, Any]) -> bool:
    props = {
        "floor_number", "security_level", "device_name",
        "is_entry", "is_exit", "is_restricted",
        "confidence", "ai_reasoning", "device_id",
        "is_elevator", "is_stairwell", "is_fire_escape"
    }
    return any(p in d for p in props)


def _sanitize_csv_value(v: Any) -> str:
    if v is None:
        return ""
    s = str(v)
    try:
        s.encode("utf-8")
        return s
    except UnicodeEncodeError:
        return s.encode("utf-8", errors="replace").decode("utf-8")


def _parse_ai_extraction(d: Dict[str, Any]) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, str) and ";" in v:
            parsed.update(_parse_bundled_extraction_string(v))
        else:
            parsed[k] = v
    return parsed


def _parse_bundled_extraction_string(txt: Any) -> Dict[str, Any]:
    parsed = {
        "floor_number":   "",
        "security_level": "",
        "is_entry":       False,
        "is_exit":        False,
        "is_restricted":  False,
        "confidence":     1.0,
        "device_name":    "",
        "source":         "ai_extracted",
        "saved_at":       ""
    }
    if not isinstance(txt, str):
        return parsed

    m = re.search(r"Floor\s+(\d+)", txt, re.IGNORECASE)
    if m:
        parsed["floor_number"] = int(m.group(1))

    m = re.search(r"Security level\s+(\d+)", txt, re.IGNORECASE)
    if m:
        parsed["security_level"] = int(m.group(1))

    if re.search(r"entry|entrance|in\b", txt, re.IGNORECASE):
        parsed["is_entry"] = True
    if re.search(r"exit|out\b", txt, re.IGNORECASE):
        parsed["is_exit"] = True
    if re.search(r"restricted|secure|private", txt, re.IGNORECASE):
        parsed["is_restricted"] = True

    # attempt to pull out a device name
    for pat in [
        r"^([^-;]+?)(?:\s*-\s*(?:Floor|Security|extracted|matched|detected))",
        r"Generated readable name[:\s]+([^;]+)",
        r"Device[:\s]+([^;]+)",
        r"Location[:\s]+([^;]+)"
    ]:
        mm = re.search(pat, txt, re.IGNORECASE)
        if mm:
            parsed["device_name"] = mm.group(1).strip()
            break

    if not parsed["device_name"]:
        first = re.split(r"[;-]|\s+(?:extracted|matched|detected)", txt)[0].strip()
        if len(first) > 2:
            parsed["device_name"] = first

    found = (
        bool(parsed["floor_number"]) +
        bool(parsed["security_level"]) +
        int(parsed["is_entry"] or parsed["is_exit"]) +
        bool(parsed["device_name"])
    )
    parsed["confidence"] = min(1.0, found / 4.0)
    return parsed


def _bootstrap_enhanced_data() -> None:
    """Ensure there’s always at least one mapping entry on import."""
    try:
        svc = get_learning_service()
        if not svc.learned_data:
            dev = get_device_learning_data()
            if dev:
                fp = "bootstrap_consolidated"
                svc.learned_data[fp] = {
                    "filename":        "consolidated_device_data.csv",
                    "saved_at":        datetime.now().isoformat(),
                    "source":          "bootstrap",
                    "device_count":    len(dev),
                    "device_mappings": dev,
                    "column_mappings": {}
                }
                svc._persist_learned_data()
    except Exception:
        pass


# run bootstrap at import
_bootstrap_enhanced_data()


__all__ = [
    "get_enhanced_data",
    "get_device_learning_data",
    "to_json_string",
    "to_csv_string",
]
