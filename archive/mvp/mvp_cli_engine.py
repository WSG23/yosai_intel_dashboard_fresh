from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

from mvp.data_verification_component import DataVerificationComponent
from mvp.unicode_fix_module import (
    clean_text,
    safe_file_read,
    safe_file_write,
    sanitize_dataframe,
)

try:
    from core.security_validator import SecurityValidator
except Exception:
    SecurityValidator = None

try:
    from services.data_processing.unified_upload_validator import UnifiedUploadValidator
except Exception:
    UnifiedUploadValidator = None

try:
    from services.data_processing.processor import Processor
except Exception:
    Processor = None

try:
    from services.data_processing.analytics_engine import AnalyticsEngine
except Exception:
    AnalyticsEngine = None


def load_dataframe(path: Path, debug: bool = False) -> pd.DataFrame:
    """Load a CSV/JSON/Excel file with encoding fallbacks."""
    if UnifiedUploadValidator:
        validator = UnifiedUploadValidator()
        result = validator.validate_file_upload(str(path))
        if not result.valid:
            raise ValueError(f"Validation failed: {result.reason}")
    text = safe_file_read(path)
    if path.suffix.lower() == ".json":
        df = pd.read_json(text)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df = sanitize_dataframe(df)
    return df


def generate_analytics(df: pd.DataFrame) -> dict:
    if AnalyticsEngine:
        try:
            engine = AnalyticsEngine()
            return engine.analyze_dataframe(df)
        except Exception:
            pass
    try:
        from services.analytics_summary import analyze_dataframe

        return analyze_dataframe(df)
    except Exception:
        return {"rows": len(df)}


def process_file(
    filepath: Path, output: Path, validate_only: bool, debug: bool
) -> None:
    if debug:
        logger.info("Processing %s -> %s", filepath, output)
    df = load_dataframe(filepath, debug=debug)
    verifier = DataVerificationComponent()
    df, mapping = verifier.verify_dataframe(df)
    if validate_only:
        logger.info("Validation complete. Exiting due to --validate-only flag.")
        return
    if Processor:
        try:
            processor = Processor()
            df = processor.validator.validate(df)
        except Exception:
            pass
    analytics = generate_analytics(df)
    out_file = output / f"{filepath.stem}_analytics.json"
    safe_file_write(out_file, json.dumps(analytics, indent=2))
    verifier.save_verification(mapping, output / f"{filepath.stem}_verification.json")
    logger.info("✅ Results saved to %s", output)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="MVP CLI Engine")
    parser.add_argument("file", help="Path to input file")
    parser.add_argument("--output", default="mvp_output", help="Output directory")
    parser.add_argument(
        "--validate-only", action="store_true", help="Only run validation steps"
    )
    parser.add_argument("--debug", action="store_true", help="Verbose output")
    args = parser.parse_args(argv)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        process_file(Path(args.file), output_dir, args.validate_only, args.debug)
    except Exception as exc:
        if args.debug:
            import traceback

            traceback.print_exc()
        logger.error("❌ Processing failed: %s", clean_text(str(exc)))


if __name__ == "__main__":
    main()
