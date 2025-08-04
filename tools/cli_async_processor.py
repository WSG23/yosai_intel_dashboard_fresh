#!/usr/bin/env python3
"""
AsyncFileProcessor CLI - Test full service layer in isolation
Usage: python tools/cli_async_processor.py <file_path> [--verbose]
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


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI tool"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=level
    )


async def process_file_with_service(
    file_path: str, verbose: bool = False
) -> Dict[str, Any]:
    """Process a file using the full AsyncFileProcessor service"""
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

        logger.info(f"Processing file with AsyncFileProcessor: {file_path}")

        # Import and create AsyncFileProcessor
        from yosai_intel_dashboard.src.services.data_processing.async_file_processor import (
            AsyncFileProcessor,
        )
        from yosai_intel_dashboard.src.infrastructure.callbacks import (
            CallbackType,
            UnifiedCallbackRegistry,
        )

        registry = UnifiedCallbackRegistry()
        processor = AsyncFileProcessor(callback_registry=registry)

        # Read file content and encode as base64 (like your upload system)
        with open(path, "rb") as f:
            content = f.read()

        content_b64 = base64.b64encode(content).decode("utf-8")
        content_with_prefix = f"data:application/octet-stream;base64,{content_b64}"

        logger.info(f"File size: {len(content):,} bytes")
        logger.info(f"File extension: {path.suffix}")

        # Progress callback to track processing
        progress_data = {"last_progress": 0}

        def progress_callback(progress: int) -> None:
            if progress != progress_data["last_progress"]:
                logger.info(f"Processing progress: {progress}%")
                progress_data["last_progress"] = progress

        registry.register_callback(
            CallbackType.PROGRESS, progress_callback, component_id=path.name
        )

        # Process file with AsyncFileProcessor
        logger.info("Starting AsyncFileProcessor...")
        df = await processor.process_file(content_with_prefix, path.name)

        # Gather results
        result = {
            "success": True,
            "processor": "AsyncFileProcessor",
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
            f"AsyncFileProcessor succeeded: {len(df)} rows, {len(df.columns)} columns"
        )
        return result

    except Exception as e:
        logger.error(f"AsyncFileProcessor failed: {str(e)}")
        if verbose:
            logger.error(traceback.format_exc())

        return {
            "success": False,
            "processor": "AsyncFileProcessor",
            "error": str(e),
            "error_type": type(e).__name__,
            "file_path": file_path,
            "traceback": traceback.format_exc() if verbose else None,
        }


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Test AsyncFileProcessor service in isolation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/cli_async_processor.py test_unicode_upload.csv --verbose
  python tools/cli_async_processor.py temp/uploaded_data/Enhanced_Security_Demo.csv.parquet
        """,
    )

    parser.add_argument("file_path", help="Path to the file to process")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Process the file
    result = asyncio.run(process_file_with_service(args.file_path, args.verbose))

    # Output results
    print(json.dumps(result, indent=2, default=str))

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
