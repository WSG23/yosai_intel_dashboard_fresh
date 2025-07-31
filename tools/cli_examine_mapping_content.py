#!/usr/bin/env python3
"""
Examine actual content of learned mappings
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    try:
        from yosai_intel_dashboard.src.services.device_learning_service import DeviceLearningService

        device_service = DeviceLearningService()
        learned_mappings_dict = device_service.learned_mappings

        print("=== EXAMINING MAPPING CONTENT IN DETAIL ===")

        # Focus on Enhanced_Security_Demo mappings (our target data)
        enhanced_mappings = [
            (key, value)
            for key, value in learned_mappings_dict.items()
            if "Enhanced_Security_Demo" in str(value.get("filename", ""))
        ]

        print(f"Found {len(enhanced_mappings)} Enhanced_Security_Demo mappings")

        for i, (key, mapping) in enumerate(enhanced_mappings):
            print(f"\n=== Enhanced Security Demo Mapping {i+1}: {key} ===")
            print(f"Filename: {mapping.get('filename')}")
            print(f"Saved at: {mapping.get('saved_at')}")
            print(f"Device count: {mapping.get('device_count', 0)}")

            # Examine column mappings
            if "mappings" in mapping:
                print(f"\n--- Column Mappings ---")
                mappings = mapping["mappings"]
                print(f"Mappings type: {type(mappings)}")
                if isinstance(mappings, dict):
                    for col, field in mappings.items():
                        print(f"  {col} → {field}")
                else:
                    print(f"Mappings content: {mappings}")

            # Examine device mappings
            if "device_mappings" in mapping:
                print(f"\n--- Device Mappings ---")
                device_mappings = mapping["device_mappings"]
                print(f"Device mappings type: {type(device_mappings)}")
                if isinstance(device_mappings, dict):
                    print(f"Device mapping keys: {list(device_mappings.keys())[:5]}")
                    # Show sample device mappings
                    for device, person in list(device_mappings.items())[:3]:
                        print(f"  {device} → {person}")
                    if len(device_mappings) > 3:
                        print(
                            f"  ... and {len(device_mappings) - 3} more device mappings"
                        )
                else:
                    print(f"Device mappings content: {device_mappings}")

        # Also examine one other mapping for comparison
        print(f"\n=== EXAMINING ONE KEY FOB MAPPING ===")
        key_fob_mappings = [
            (key, value)
            for key, value in learned_mappings_dict.items()
            if "key_fob" in str(value.get("filename", ""))
        ]

        if key_fob_mappings:
            key, mapping = key_fob_mappings[0]
            print(f"Key fob mapping: {mapping.get('filename')}")

            if "mappings" in mapping:
                print(f"Column mappings: {mapping['mappings']}")

            if "device_mappings" in mapping:
                device_mappings = mapping["device_mappings"]
                if isinstance(device_mappings, dict) and len(device_mappings) > 0:
                    print(f"Sample device mappings:")
                    for device, person in list(device_mappings.items())[:2]:
                        print(f"  {device} → {person}")

    except Exception as e:
        print(f"Error examining mapping content: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
