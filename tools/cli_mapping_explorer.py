#!/usr/bin/env python3
"""
Enhanced Mapping Explorer - Test DeviceLearningService methods in detail
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=level
    )


async def explore_mapping_services(file_path: str, verbose: bool = False) -> dict:
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    try:
        logger.info("=== ENHANCED MAPPING SERVICE EXPLORATION ===")

        # Process file first
        import base64

        from yosai_intel_dashboard.src.services.data_processing.async_file_processor import AsyncFileProcessor

        path = Path(file_path)
        filename = path.name

        with open(path, "rb") as f:
            content = f.read()

        content_b64 = base64.b64encode(content).decode("utf-8")
        content_with_prefix = f"data:application/octet-stream;base64,{content_b64}"

        processor = AsyncFileProcessor()
        df = await processor.process_file(content_with_prefix, filename)

        logger.info(f"Processed: {len(df)} rows, {list(df.columns)}")

        result = {
            "success": True,
            "file_info": {"rows": len(df), "columns": list(df.columns)},
        }

        # Explore AI Suggestions in detail
        logger.info("=== AI SUGGESTIONS DETAILED ===")
        from services.data_enhancer.mapping_utils import get_ai_column_suggestions

        suggestions = get_ai_column_suggestions(df)

        result["ai_suggestions_detailed"] = suggestions
        logger.info(f"AI Suggestions: {json.dumps(suggestions, indent=2)}")

        # Explore DeviceLearningService methods with correct parameters
        logger.info("=== DEVICE LEARNING SERVICE EXPLORATION ===")
        from services.device_learning_service import DeviceLearningService

        device_service = DeviceLearningService()

        # Test get_learned_mappings with df and filename
        try:
            learned_mappings = device_service.get_learned_mappings(df, filename)
            logger.info(f"Learned mappings result: {type(learned_mappings)}")
            if isinstance(learned_mappings, dict):
                logger.info(
                    f"Learned mappings keys: {list(learned_mappings.keys())[:5]}"
                )
                result["learned_mappings"] = {
                    "count": len(learned_mappings),
                    "keys": list(learned_mappings.keys())[:5],
                }
            else:
                result["learned_mappings"] = {
                    "type": str(type(learned_mappings)),
                    "value": str(learned_mappings)[:200],
                }
        except Exception as e:
            logger.warning(f"get_learned_mappings failed: {e}")
            result["learned_mappings"] = {"error": str(e)}

        # Test get_user_device_mappings with filename
        try:
            user_device_mappings = device_service.get_user_device_mappings(filename)
            logger.info(f"User device mappings result: {type(user_device_mappings)}")
            if isinstance(user_device_mappings, dict):
                result["user_device_mappings"] = {
                    "count": len(user_device_mappings),
                    "sample": list(user_device_mappings.keys())[:3],
                }
            else:
                result["user_device_mappings"] = {
                    "type": str(type(user_device_mappings)),
                    "value": str(user_device_mappings)[:200],
                }
        except Exception as e:
            logger.warning(f"get_user_device_mappings failed: {e}")
            result["user_device_mappings"] = {"error": str(e)}

        # Test other available methods
        available_methods = [
            method for method in dir(device_service) if not method.startswith("_")
        ]
        result["available_methods"] = available_methods
        logger.info(f"Available methods: {available_methods}")

        logger.info("=== EXPLORATION COMPLETE ===")
        return result

    except Exception as e:
        logger.error(f"Exploration failed: {e}")
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Explore mapping services in detail")
    parser.add_argument("file_path", help="Path to file (CSV/JSON only)")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()
    result = asyncio.run(explore_mapping_services(args.file_path, args.verbose))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
