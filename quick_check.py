#!/usr/bin/env python3
"""
Quick check of device mapping persistence
"""

import os
import json
from pathlib import Path
from datetime import datetime


def quick_check():
    """Quick verification of what's actually saved."""

    print("🔍 QUICK DEVICE MAPPING CHECK")
    print("=" * 40)

    # Check storage directory
    storage_dir = Path("data/device_learning")
    print(f"📂 Storage: {storage_dir.absolute()}")
    print(f"📂 Exists: {storage_dir.exists()}")

    if not storage_dir.exists():
        print("❌ Storage directory doesn't exist!")
        return

    # List all mapping files
    mapping_files = list(storage_dir.glob("mapping_*.json"))
    print(f"📄 Files: {len(mapping_files)}")

    if not mapping_files:
        print("❌ No mapping files found!")
        return

    # Show details of each file
    total_devices = 0
    for i, file_path in enumerate(mapping_files, 1):
        size = file_path.stat().st_size
        modified = datetime.fromtimestamp(file_path.stat().st_mtime)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            filename = data.get("filename", "Unknown")
            device_count = data.get("device_count", 0)
            saved_at = data.get("saved_at", "Unknown")
            source = data.get("source", "Unknown")

            # Check both key structures
            mappings = data.get("device_mappings", {}) or data.get("mappings", {})
            actual_count = len(mappings)
            total_devices += actual_count

            print(f"\n📄 File {i}: {file_path.name}")
            print(f"   Original: {filename}")
            print(f"   Size: {size} bytes")
            print(f"   Modified: {modified}")
            print(f"   Saved: {saved_at}")
            print(f"   Source: {source}")
            print(f"   Reported devices: {device_count}")
            print(f"   Actual devices: {actual_count}")

            if mappings:
                print(f"   Sample devices:")
                for j, (device, mapping) in enumerate(list(mappings.items())[:3], 1):
                    floor = mapping.get("floor_number", "N/A")
                    security = mapping.get("security_level", "N/A")
                    print(f"     {j}. {device} (floor: {floor}, security: {security})")
            else:
                print(f"   ❌ No device mappings found in file!")

        except Exception as e:
            print(f"\n📄 File {i}: {file_path.name}")
            print(f"   ❌ Error reading: {e}")

    print(f"\n📊 SUMMARY")
    print(f"   Total files: {len(mapping_files)}")
    print(f"   Total devices: {total_devices}")

    # Check in-memory state if possible
    try:
        from services.device_learning_service import get_device_learning_service

        service = get_device_learning_service()
        print(f"   In-memory mappings: {len(service.learned_mappings)}")

        # Check global store
        try:
            from services.ai_mapping_store import ai_mapping_store

            store_data = ai_mapping_store.all()
            print(f"   Global store items: {len(store_data)}")
        except:
            print(f"   Global store: Not available")

    except Exception as e:
        print(f"   Service check failed: {e}")


if __name__ == "__main__":
    quick_check()
