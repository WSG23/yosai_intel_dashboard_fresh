#!/usr/bin/env python3
"""
Minimal CLI File Processor - Test file processing in isolation
Usage: python tools/cli_file_processor.py <file_path> [--verbose]
"""

import argparse
import asyncio
import base64
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


def process_file_simple(file_path: str, verbose: bool = False) -> Dict[str, Any]:
    """Process a file directly using pandas and basic error handling"""
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

        logger.info(f"Processing file: {file_path}")

        # Read file content
        with open(path, "rb") as f:
            content = f.read()

        logger.info(f"File size: {len(content):,} bytes")
        logger.info(f"File extension: {path.suffix}")

        # Basic pandas processing (bypassing broken service imports)
        import pandas as pd

        logger.info("Using direct pandas processing...")

        if path.suffix.lower() == ".csv":
            # Handle CSV with encoding detection
            try:
                df = pd.read_csv(
                    path, encoding="utf-8", dtype=str, keep_default_na=False
                )
            except UnicodeDecodeError:
                logger.info("UTF-8 failed, trying with encoding detection")
                import chardet

                detected = chardet.detect(content)
                encoding = detected.get("encoding", "latin-1")
                logger.info(f"Detected encoding: {encoding}")
                df = pd.read_csv(
                    path, encoding=encoding, dtype=str, keep_default_na=False
                )

        elif path.suffix.lower() == ".json":
            df = pd.read_json(path)

        elif path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(path)

        elif path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
            logger.info("Successfully read parquet file")

        else:
            # Try to detect format by content
            try:
                # Try JSON first
                df = pd.read_json(path)
                logger.info("Detected as JSON file")
            except:
                try:
                    # Try CSV
                    df = pd.read_csv(
                        path, encoding="utf-8", dtype=str, keep_default_na=False
                    )
                    logger.info("Detected as CSV file")
                except:
                    raise ValueError(f"Cannot determine file format for: {path.suffix}")

        # Gather results
        result = {
            "success": True,
            "file_path": file_path,
            "file_size_bytes": len(content),
            "file_extension": path.suffix,
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
        logger.error(f"Error processing file: {safe_text(e)}")
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
        description="Test file processing in isolation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/cli_file_processor.py test_unicode_upload.csv
  python tools/cli_file_processor.py test_unicode_upload.csv --verbose
  python tools/cli_file_processor.py temp/uploaded_data/Enhanced_Security_Demo.csv.parquet
        """,
    )

    parser.add_argument("file_path", help="Path to the file to process")

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging and show full tracebacks",
    )

    args = parser.parse_args()

    # Process the file
    result = process_file_simple(args.file_path, args.verbose)

    # Output results
    print(json.dumps(result, indent=2, default=str))

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
