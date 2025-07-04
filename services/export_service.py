"""Export helpers for enhanced learning data."""
import json
import re
from typing import Dict, Any, List
from datetime import datetime
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
        # Filter and clean up learned data to avoid nested fingerprints
        for fingerprint, content in learning_service.learned_data.items():
            if isinstance(content, dict) and content.get('filename'):
                # This looks like valid learned data, keep it
                enhanced_data[fingerprint] = content
    
    # Get from device learning service as fallback/supplement
    device_service = get_device_learning_service()
    if hasattr(device_service, 'learned_mappings') and device_service.learned_mappings:
        # Create a single consolidated entry for all device mappings
        device_mappings = device_service.learned_mappings
        if device_mappings:
            fingerprint = "device_learning_consolidated"
            enhanced_data[fingerprint] = {
                "fingerprint": fingerprint,
                "filename": "device_learning_mappings.csv",
                "saved_at": datetime.now().isoformat(),
                "source": "device_learning",
                "device_count": len(device_mappings),
                "device_mappings": device_mappings,
                "column_mappings": {}
            }
    
    # Try to get from global AI mapping store as additional source
    try:
        from services.ai_mapping_store import ai_mapping_store
        if hasattr(ai_mapping_store, 'all') and ai_mapping_store.all():
            ai_mappings = ai_mapping_store.all()
            if ai_mappings:
                fingerprint = "ai_mapping_store_consolidated"
                enhanced_data[fingerprint] = {
                    "fingerprint": fingerprint,
                    "filename": "ai_mappings.csv",
                    "saved_at": datetime.now().isoformat(),
                    "source": "ai_mapping_store", 
                    "device_count": len(ai_mappings),
                    "device_mappings": ai_mappings,
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
        
        # Extract actual device mappings - only meaningful device names
        device_mappings = content.get("device_mappings", {})
        clean_devices = _get_clean_device_mappings(device_mappings)
        
        # Add flattened device mappings for clean devices only
        for device_id, device_data in clean_devices.items():
            if isinstance(device_data, dict):
                # Parse and separate bundled AI extraction results
                parsed_data = _parse_ai_extraction(device_data)
                
                # Create mappings.{device_id}.{property} columns with separated data
                for prop, value in parsed_data.items():
                    if value is not None and value != "":  # Only add non-empty values
                        mappings_key = f"mappings.{device_id}.{prop}"
                        device_mappings_key = f"device_mappings.{device_id}.{prop}"
                        record[mappings_key] = _sanitize_csv_value(value)
                        record[device_mappings_key] = _sanitize_csv_value(value)
            elif isinstance(device_data, str):
                # Handle bundled string data directly
                parsed_data = _parse_bundled_extraction_string(device_data)
                for prop, value in parsed_data.items():
                    if value is not None and value != "":
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


def _get_clean_device_mappings(device_mappings: dict) -> dict:
    """Extract only clean device mappings, ignoring fingerprints and metadata."""
    clean_devices = {}
    
    for key, value in device_mappings.items():
        # Skip if key looks like a fingerprint (12+ hex chars)
        if _is_fingerprint(key):
            continue
            
        # Skip if key contains metadata indicators
        if any(indicator in key.lower() for indicator in ['user_devices', 'filename', 'saved_at']):
            continue
            
        if isinstance(value, dict):
            # Check if this is actual device data (has device properties)
            if _has_device_properties(value):
                clean_devices[key] = value
            # Otherwise, recursively search for clean devices
            else:
                nested_clean = _get_clean_device_mappings(value)
                clean_devices.update(nested_clean)
        elif isinstance(value, str):
            # Handle bundled string data that contains device info
            if any(indicator in value.lower() for indicator in ['floor', 'security', 'entry', 'exit']):
                clean_devices[key] = value
    
    return clean_devices


def _is_fingerprint(key: str) -> bool:
    """Check if a key looks like a fingerprint (hex string)."""
    if not isinstance(key, str):
        return False
    
    # Fingerprints are typically 8-32 character hex strings
    if len(key) < 8 or len(key) > 32:
        return False
        
    # Check if it's all hex characters
    try:
        int(key, 16)
        return True
    except ValueError:
        return False


def _has_device_properties(data: dict) -> bool:
    """Check if dict contains actual device properties."""
    device_props = [
        'floor_number', 'security_level', 'device_name', 'is_entry', 'is_exit', 
        'is_restricted', 'confidence', 'ai_reasoning', 'device_id', 'is_elevator',
        'is_stairwell', 'is_fire_escape'
    ]
    
    return any(prop in data for prop in device_props)


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


def _parse_ai_extraction(device_data: dict) -> dict:
    """Parse device data that may contain bundled AI extraction results."""
    parsed = {}
    
    for key, value in device_data.items():
        if isinstance(value, str) and ';' in value:
            # This looks like bundled extraction results
            bundled_data = _parse_bundled_extraction_string(value)
            parsed.update(bundled_data)
        else:
            # Regular key-value pair
            parsed[key] = value
    
    return parsed


def _parse_bundled_extraction_string(bundled_str: str) -> dict:
    """Parse bundled AI extraction string into separate properties."""
    import re
    
    parsed = {
        'floor_number': '',
        'security_level': '',
        'is_entry': False,
        'is_exit': False,
        'is_restricted': False,
        'confidence': 1.0,
        'device_name': '',
        'source': 'ai_extracted',
        'saved_at': ''
    }
    
    if not isinstance(bundled_str, str):
        return parsed
    
    # Extract floor number
    floor_match = re.search(r'Floor\s+(\d+)', bundled_str, re.IGNORECASE)
    if floor_match:
        parsed['floor_number'] = int(floor_match.group(1))
    
    # Extract security level
    security_match = re.search(r'Security level\s+(\d+)', bundled_str, re.IGNORECASE)
    if security_match:
        parsed['security_level'] = int(security_match.group(1))
    
    # Detect entry/exit
    if re.search(r'entry|entrance|in\b', bundled_str, re.IGNORECASE):
        parsed['is_entry'] = True
    if re.search(r'exit|out\b', bundled_str, re.IGNORECASE):
        parsed['is_exit'] = True
        
    # Detect if restricted
    if re.search(r'restricted|secure|private', bundled_str, re.IGNORECASE):
        parsed['is_restricted'] = True
        
    # Extract device/location name - look for patterns before common extraction phrases
    name_patterns = [
        r'^([^-;]+?)(?:\s*-\s*(?:Floor|Security|extracted|matched|detected))',
        r'Generated readable name[:\s]+([^;]+)',
        r'Device[:\s]+([^;]+)',
        r'Location[:\s]+([^;]+)'
    ]
    
    for pattern in name_patterns:
        name_match = re.search(pattern, bundled_str, re.IGNORECASE)
        if name_match:
            parsed['device_name'] = name_match.group(1).strip()
            break
    
    # If no name found, try to extract from the beginning of the string
    if not parsed['device_name']:
        # Take first part before any extraction indicators
        first_part = re.split(r'[;-]|\s+(?:extracted|matched|detected)', bundled_str)[0].strip()
        if first_part and len(first_part) > 2:
            parsed['device_name'] = first_part
    
    # Set confidence based on number of extracted features
    features_found = sum([
        bool(parsed['floor_number']),
        bool(parsed['security_level']),
        bool(parsed['is_entry'] or parsed['is_exit']),
        bool(parsed['device_name'])
    ])
    parsed['confidence'] = min(1.0, features_found / 4.0)
    
    return parsed


# Consolidate current data when module loads to ensure exports have content
def _bootstrap_enhanced_data():
    """Bootstrap enhanced data by consolidating from all available sources."""
    try:
        learning_service = get_learning_service()
        if not learning_service.learned_data:
            # Try to populate from device learning service
            device_data = get_device_learning_data()
            if device_data:
                # Create a single consolidated entry instead of individual entries
                fingerprint = "bootstrap_consolidated"
                enhanced_entry = {
                    "filename": "consolidated_device_data.csv", 
                    "saved_at": datetime.now().isoformat(),
                    "source": "bootstrap",
                    "device_count": len(device_data),
                    "device_mappings": device_data,  # Direct mapping, no nesting
                    "column_mappings": {}
                }
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