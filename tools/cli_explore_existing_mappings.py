#!/usr/bin/env python3
"""
Explore existing learned mappings in detail
"""

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    try:
        from yosai_intel_dashboard.src.services.device_learning_service import DeviceLearningService

        device_service = DeviceLearningService()

        logger.info("=== EXPLORING EXISTING LEARNED MAPPINGS ===")

        # Get the learned_mappings property (not the method)
        learned_mappings_dict = device_service.learned_mappings
        logger.info(f"Total learned mappings in memory: {len(learned_mappings_dict)}")

        # Show details of each mapping
        for i, (key, value) in enumerate(learned_mappings_dict.items()):
            logger.info(f"\n--- Mapping {i+1}: {key} ---")
            logger.info(f"Type: {type(value)}")
            if isinstance(value, dict):
                logger.info(f"Keys: {list(value.keys())}")
                # Show a sample of the mapping data
                for subkey, subvalue in list(value.items())[:3]:
                    logger.info(f"  {subkey}: {subvalue}")
                if len(value) > 3:
                    logger.info(f"  ... and {len(value) - 3} more items")
            else:
                logger.info(f"Value: {value}")

        # Test get_device_mapping_by_name with known patterns
        logger.info(f"\n=== TESTING DEVICE MAPPING SEARCH ===")
        test_names = [
            "Employee Code",
            "Access Card",
            "Door Location",
            "person_id",
            "door_id",
            "Name",
        ]

        for name in test_names:
            try:
                mapping = device_service.get_device_mapping_by_name(name)
                logger.info(f"{name}: {mapping}")
            except Exception as e:
                logger.error(f"{name}: Error - {e}")

    except Exception as e:
        logger.error(f"Error exploring mappings: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
