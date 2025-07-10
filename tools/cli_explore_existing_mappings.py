#!/usr/bin/env python3
"""
Explore existing learned mappings in detail
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    try:
        from services.device_learning_service import DeviceLearningService
        
        device_service = DeviceLearningService()
        
        print("=== EXPLORING EXISTING LEARNED MAPPINGS ===")
        
        # Get the learned_mappings property (not the method)
        learned_mappings_dict = device_service.learned_mappings
        print(f"Total learned mappings in memory: {len(learned_mappings_dict)}")
        
        # Show details of each mapping
        for i, (key, value) in enumerate(learned_mappings_dict.items()):
            print(f"\n--- Mapping {i+1}: {key} ---")
            print(f"Type: {type(value)}")
            if isinstance(value, dict):
                print(f"Keys: {list(value.keys())}")
                # Show a sample of the mapping data
                for subkey, subvalue in list(value.items())[:3]:
                    print(f"  {subkey}: {subvalue}")
                if len(value) > 3:
                    print(f"  ... and {len(value) - 3} more items")
            else:
                print(f"Value: {value}")
        
        # Test get_device_mapping_by_name with known patterns
        print(f"\n=== TESTING DEVICE MAPPING SEARCH ===")
        test_names = ["Employee Code", "Access Card", "Door Location", "person_id", "door_id", "Name"]
        
        for name in test_names:
            try:
                mapping = device_service.get_device_mapping_by_name(name)
                print(f"{name}: {mapping}")
            except Exception as e:
                print(f"{name}: Error - {e}")
        
    except Exception as e:
        print(f"Error exploring mappings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
