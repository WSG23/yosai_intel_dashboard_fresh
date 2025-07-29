# debug_live_upload.py - Add this to your project and run it
#!/usr/bin/env python3
"""
LIVE UPLOAD DEBUGGING - Find where 150 row truncation happens
Add this temporarily to trace the upload pipeline
"""

import logging
import sys

sys.path.append(".")

logger = logging.getLogger(__name__)


def add_debug_hooks():
    """Add debugging hooks to track data flow"""

    # Hook 1: Patch process_uploaded_file
    from services import upload_service

    original_process = upload_service.process_uploaded_file

    def debug_process_uploaded_file(contents, filename):
        logger.info(f"🚀 HOOK 1: process_uploaded_file() called for {filename}")
        result = original_process(contents, filename)
        if result.get("success"):
            rows = result.get("rows", 0)
            logger.info(f"🎯 HOOK 1: process_uploaded_file() result: {rows} rows")
            if rows == 150:
                logger.error(f"🚨 FOUND 150 ROW LIMIT in process_uploaded_file!")
        return result

    upload_service.process_uploaded_file = debug_process_uploaded_file

    # Hook 2: Patch FileHandler.process_base64_contents
    from services.data_processing.file_handler import FileHandler

    original_validate = FileHandler.process_base64_contents

    def debug_validate_file_contents(self, contents, filename):
        logger.info(
            f"🔒 HOOK 2: FileHandler.process_base64_contents() for {filename}"
        )
        df = original_validate(self, contents, filename)
        rows = len(df)
        logger.info(f"🎯 HOOK 2: FileHandler result: {rows} rows")
        if rows == 150:
            logger.error(f"🚨 FOUND 150 ROW LIMIT in FileHandler!")
        return df

    FileHandler.process_base64_contents = debug_validate_file_contents

    # Hook 3: Patch utils.file_validator.process_dataframe
    from utils import file_validator

    original_process_df = file_validator.process_dataframe

    def debug_process_dataframe(decoded, filename):
        logger.info(
            f"📊 HOOK 3: process_dataframe() for {filename} ({len(decoded)} bytes)"
        )
        df, err = original_process_df(decoded, filename)
        if df is not None:
            rows = len(df)
            logger.info(f"🎯 HOOK 3: process_dataframe() result: {rows} rows")
            if rows == 150:
                logger.error(f"🚨 FOUND 150 ROW LIMIT in process_dataframe!")
        return df, err

    file_validator.process_dataframe = debug_process_dataframe

    # Hook 4: Patch FileProcessor.process_uploaded_contents if available
    try:
        from services.data_processing.file_processor import FileProcessor

        original_process = FileProcessor.process_uploaded_contents

        def debug_validate_data(self, df):
            input_rows = len(df)
            logger.info(
                f"🧹 HOOK 4: FileProcessor.process_uploaded_contents() input: {input_rows} rows"
            )
            result = original_process(self, df)
            if result.get("valid") and result.get("data") is not None:
                output_rows = len(result["data"])
                logger.info(
                    f"🎯 HOOK 4: FileProcessor.process_uploaded_contents() output: {output_rows} rows"
                )
                if output_rows == 150:
                    logger.error(
                        f"🚨 FOUND 150 ROW LIMIT in FileProcessor.process_uploaded_contents!"
                    )
                if output_rows != input_rows:
                    logger.warning(
                        f"⚠️ HOOK 4: Data loss: {input_rows} → {output_rows} rows"
                    )
            return result

        FileProcessor.process_uploaded_contents = debug_validate_data
        logger.info("✅ Added FileProcessor debugging hook")
    except ImportError:
        logger.info("⏭️ FileProcessor not available for debugging")

    logger.info("🔍 All debugging hooks installed!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="🔍 %(levelname)s: %(message)s")
    add_debug_hooks()
    logger.info(
        "🚀 Upload debugging hooks installed. Upload a file and check the logs!"
    )
