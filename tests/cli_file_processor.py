#!/usr/bin/env python3
"""
CLI File Processor Tool - Test FileProcessorService in isolation
Usage: python tools/cli_file_processor.py <file_path> [--verbose] [--output json|csv]
"""

import argparse
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict

# Add project root to path so we can import services
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import create_config_manager
from services.upload.service_registration import register_upload_services
from core.service_container import ServiceContainer
from services.file_processor_service import FileProcessorService


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI tool"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=level
    )


def create_cli_container() -> ServiceContainer:
    """Create a DI container with minimal services for CLI testing"""
    container = ServiceContainer()

    # Register configuration
    config_manager = create_config_manager()
    container.register("config", config_manager)

    # Register only the services we need for file processing
    register_upload_services(container)

    return container


def process_file_cli(file_path: str, verbose: bool = False) -> Dict[str, Any]:
    """Process a file using the existing FileProcessorService"""
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    try:
        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": file_path,
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}",
                "file_path": file_path,
            }

        # Create container and get file processor
        logger.info(f"Processing file: {file_path}")
        container = create_cli_container()
        file_processor = container.get("file_processor")

        # Read file content
        with open(path, "rb") as f:
            content = f.read()

        logger.info(f"File size: {len(content):,} bytes")
        logger.info(f"File extension: {path.suffix}")

        # Validate file
        validation_result = file_processor.validate_file(path.name, content)
        logger.info(f"Validation result: {validation_result}")

        if not validation_result.get("is_valid", False):
            return {
                "success": False,
                "error": "File validation failed",
                "validation_result": validation_result,
                "file_path": file_path,
            }

        # Process file
        logger.info("Processing file content...")
        df = file_processor.process_file(content, path.name)

        # Gather results
        result = {
            "success": True,
            "file_path": file_path,
            "file_size_bytes": len(content),
            "file_extension": path.suffix,
            "validation_result": validation_result,
            "dataframe_info": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                "has_null_values": df.isnull().any().any(),
                "null_counts": df.isnull().sum().to_dict(),
            },
            "sample_data": df.head(3).to_dict("records") if len(df) > 0 else [],
        }

        logger.info(
            f"Successfully processed: {len(df)} rows, {len(df.columns)} columns"
        )
        return result

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        if verbose:
            logger.error(traceback.format_exc())

        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "file_path": file_path,
            "traceback": traceback.format_exc() if verbose else None,
        }


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Test FileProcessorService in isolation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/cli_file_processor.py data/sample.csv
  python tools/cli_file_processor.py problematic_unicode.csv --verbose
  python tools/cli_file_processor.py large_file.json --output csv > results.csv
        """,
    )

    parser.add_argument("file_path", help="Path to the file to process")

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging and show full tracebacks",
    )

    parser.add_argument(
        "--output",
        "-o",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    # Process the file
    result = process_file_cli(args.file_path, args.verbose)

    # Output results
    if args.output == "json":
        print(json.dumps(result, indent=2, default=str))
    elif args.output == "csv":
        if result["success"] and "sample_data" in result:
            import pandas as pd

            if result["sample_data"]:
                df = pd.DataFrame(result["sample_data"])
                print(df.to_csv(index=False))
            else:
                print("No data to output as CSV")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
