#!/usr/bin/env python3
"""
Minimal CLI File Processor - Test file processing in isolation
Usage: python tools/cli_file_processor.py <file_path> [--verbose]
"""

import argparse
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.exceptions import FileProcessingError
from src.logging_config import setup_logging
from yosai_intel_dashboard.src.utils.text_utils import safe_text


def process_file_simple(file_path: str, verbose: bool = False) -> Dict[str, Any]:
    """Process a file directly using pandas with structured logging."""
    setup_logging(logging.DEBUG if verbose else logging.INFO)
    logger = logging.getLogger(__name__)

    path = Path(file_path)
    if not path.exists():
        raise FileProcessingError(f"File not found: {file_path}")
    if not path.is_file():
        raise FileProcessingError(f"Path is not a file: {file_path}")

    logger.info("Processing file", extra={"file_path": file_path})

    try:
        # Read file content
        with open(path, "rb") as f:
            content = f.read()

        logger.info(
            "File metadata",
            extra={"size_bytes": len(content), "extension": path.suffix},
        )

        import pandas as pd

        logger.info("Using direct pandas processing")

        if path.suffix.lower() == ".csv":
            try:
                df = pd.read_csv(path, encoding="utf-8", dtype=str, keep_default_na=False)
            except UnicodeDecodeError:
                logger.info("UTF-8 failed, trying with encoding detection")
                import chardet

                detected = chardet.detect(content)
                encoding = detected.get("encoding", "latin-1")
                logger.info("Detected encoding", extra={"encoding": encoding})
                df = pd.read_csv(path, encoding=encoding, dtype=str, keep_default_na=False)

        elif path.suffix.lower() == ".json":
            df = pd.read_json(path)

        elif path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(path)

        elif path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
            logger.info("Successfully read parquet file")

        else:
            try:
                df = pd.read_json(path)
                logger.info("Detected as JSON file")
            except (ValueError, json.JSONDecodeError):
                try:
                    df = pd.read_csv(path, encoding="utf-8", dtype=str, keep_default_na=False)
                    logger.info("Detected as CSV file")
                except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as err:
                    raise FileProcessingError(
                        f"Cannot determine file format for: {path.suffix}"
                    ) from err

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
            "Successfully processed dataframe",
            extra={"rows": len(df), "columns": len(df.columns)},
        )
        return result

    except FileProcessingError:
        raise
    except Exception as err:  # pragma: no cover - unexpected errors
        logger.error("Error processing file", exc_info=err)
        raise FileProcessingError("Error processing file") from err


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
    try:
        result = process_file_simple(args.file_path, args.verbose)
        logging.getLogger(__name__).info("Processing result", extra={"result": result})
        sys.exit(0)
    except FileProcessingError as err:
        logging.getLogger(__name__).error("Processing failed", extra={"error": str(err)})
        sys.exit(1)


if __name__ == "__main__":
    main()
