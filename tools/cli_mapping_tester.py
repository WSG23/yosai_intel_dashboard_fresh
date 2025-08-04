#!/usr/bin/env python3
"""
CLI Mapping Service Tester - Test DeviceLearningService and column mapping in isolation
Usage: python tools/cli_mapping_tester.py <file_path> [--verbose] [--suggest-only]
"""

import argparse
import asyncio
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from yosai_intel_dashboard.src.utils.text_utils import safe_text


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI tool"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=level
    )


async def test_mapping_service(
    file_path: str, verbose: bool = False, suggest_only: bool = False
) -> Dict[str, Any]:
    """Test the mapping service pipeline: file processing -> column mapping -> device learning"""
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    try:
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        logger.info(f"Testing mapping service pipeline for: {file_path}")

        # Step 1: Process file with AsyncFileProcessor
        logger.info("=== STEP 1: File Processing ===")
        from yosai_intel_dashboard.src.services.data_processing.async_file_processor import (
            AsyncFileProcessor,
        )

        processor = AsyncFileProcessor()

        with path.open("rb") as f:
            content = f.read()

        import base64

        content_b64 = base64.b64encode(content).decode("utf-8")
        content_with_prefix = f"data:application/octet-stream;base64,{content_b64}"

        df = await processor.process_file(content_with_prefix, path.name)
        logger.info(f"File processed: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")

        result = {
            "success": True,
            "file_path": file_path,
            "file_processing": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "sample_data": df.head(2).to_dict("records") if len(df) > 0 else [],
            },
        }

        # Step 2: Test AI Column Suggestions
        logger.info("=== STEP 2: AI Column Suggestions ===")
        try:
            from yosai_intel_dashboard.src.services.data_enhancer.mapping_utils import (
                get_ai_column_suggestions,
            )

            # Test AI suggestions for the columns
            suggestions = get_ai_column_suggestions(df)
            logger.info(
                f"AI suggestions generated: {len(suggestions) if suggestions else 0} suggestions"
            )

            result["ai_suggestions"] = {
                "success": True,
                "suggestions": suggestions,
                "suggestion_count": len(suggestions) if suggestions else 0,
            }

        except Exception as ai_error:
            logger.warning(f"AI suggestions failed: {safe_text(ai_error)}")
            result["ai_suggestions"] = {
                "success": False,
                "error": safe_text(ai_error),
            }

        # Step 3: Test Device Learning Service
        logger.info("=== STEP 3: Device Learning Service ===")
        try:
            from yosai_intel_dashboard.src.services.device_learning_service import (
                DeviceLearningService,
            )

            device_service = DeviceLearningService()

            # Test learning from the dataframe
            if hasattr(device_service, "learn_from_dataframe"):
                learning_result = device_service.learn_from_dataframe(df, path.name)
                logger.info(f"Device learning completed")

                result["device_learning"] = {
                    "success": True,
                    "learning_result": learning_result,
                }
            else:
                # Try other methods that might exist
                available_methods = [
                    method
                    for method in dir(device_service)
                    if not method.startswith("_")
                ]
                logger.info(f"Available device learning methods: {available_methods}")

                result["device_learning"] = {
                    "success": True,
                    "available_methods": available_methods,
                    "note": "learn_from_dataframe method not found",
                }

        except Exception as device_error:
            logger.warning(f"Device learning failed: {safe_text(device_error)}")
            result["device_learning"] = {
                "success": False,
                "error": safe_text(device_error),
            }

        # Step 4: Test Mapping Application (if not suggest-only)
        if not suggest_only:
            logger.info("=== STEP 4: Mapping Application ===")
            try:
                # Test applying existing mappings
                mappings_file = Path("data/learned_mappings.json")
                if mappings_file.exists():
                    with mappings_file.open(encoding="utf-8") as f:
                        mappings_data = json.load(f)

                    result["mapping_application"] = {
                        "success": True,
                        "mappings_from_file": True,
                        "mappings_data_keys": (
                            list(mappings_data.keys()) if mappings_data else []
                        ),
                    }
                else:
                    result["mapping_application"] = {
                        "success": False,
                        "error": "No learned_mappings.json found",
                    }

            except Exception as app_error:
                logger.warning(f"Mapping application failed: {safe_text(app_error)}")
                result["mapping_application"] = {
                    "success": False,
                    "error": safe_text(app_error),
                }

        logger.info("=== MAPPING SERVICE PIPELINE COMPLETE ===")
        return result

    except Exception as e:
        logger.error(f"Mapping service pipeline failed: {safe_text(e)}")
        if verbose:
            logger.error(traceback.format_exc())

        return {
            "success": False,
            "error": safe_text(e),
            "error_type": type(e).__name__,
            "file_path": file_path,
            "traceback": traceback.format_exc() if verbose else None,
        }


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Test mapping service pipeline in isolation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/cli_mapping_tester.py test_unicode_upload.csv --verbose
  python tools/cli_mapping_tester.py temp/uploaded_data/Enhanced_Security_Demo.csv.parquet --suggest-only
  python tools/cli_mapping_tester.py data/learned_mappings.json
        """,
    )

    parser.add_argument("file_path", help="Path to the file to process")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--suggest-only",
        "-s",
        action="store_true",
        help="Only test AI suggestions, skip mapping application",
    )

    args = parser.parse_args()

    # Test the mapping service
    result = asyncio.run(
        test_mapping_service(args.file_path, args.verbose, args.suggest_only)
    )

    # Output results
    print(json.dumps(result, indent=2, default=str))

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
