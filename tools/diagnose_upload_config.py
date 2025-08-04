#!/usr/bin/env python3
"""CLI for diagnosing upload configuration."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running without installation by adding project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.common.config import ConfigService
import importlib


# Prefer the new clean-architecture module path but allow tests to
# provide a lightweight stub by optionally importing the legacy module
# via ``importlib``.  This keeps compatibility for existing tests while
# avoiding the deprecated direct "config" import style.
try:  # allow tests to provide a lightweight stub
    dynamic_mod = importlib.import_module("config.dynamic_config")
except Exception:  # pragma: no cover - fallback to real implementation
    dynamic_mod = importlib.import_module(
        "yosai_intel_dashboard.src.infrastructure.config.dynamic_config"
    )

diagnose_upload_config = dynamic_mod.diagnose_upload_config
dynamic_config = dynamic_mod.dynamic_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print diagnostics for upload configuration"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show additional details"
    )
    args = parser.parse_args(argv)

    cfg = ConfigService()
    diagnose_upload_config()
    if args.verbose:
        print("--- Verbose Details ---")
        print(f"Upload chunk size: {cfg.upload_chunk_size}")
        print(f"Max parallel uploads: {dynamic_config.get_max_parallel_uploads()}")
        print(f"Validator rules: {dynamic_config.get_validator_rules()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
