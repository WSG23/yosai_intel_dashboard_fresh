#!/usr/bin/env python3
"""Setup and validate environment configuration for the dashboard."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

from config import ConfigManager


def _parse_env(path: Path) -> Dict[str, str]:
    """Parse an ``.env`` style file into a dictionary."""
    data: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def ensure_env(example: Path, target: Path) -> bool:
    """Ensure ``target`` exists. Copy from ``example`` if missing.

    Returns ``True`` if the target already existed, ``False`` if it was created.
    """
    if not target.exists():
        shutil.copy(example, target)
        print(f"Created {target} from {example}. Fill in required values.")
        return False
    return True


def verify_required_keys(example: Path, target: Path) -> bool:
    """Verify that ``target`` defines all keys present in ``example``."""
    required = _parse_env(example)
    actual = _parse_env(target)
    missing = [k for k in required if not actual.get(k)]
    if missing:
        print("Missing required environment variables in .env:")
        for key in missing:
            print(f" - {key}")
        return False
    return True


def validate_configuration() -> bool:
    """Run configuration validation using ``ConfigManager``."""
    manager = ConfigManager()
    result = manager.validate_config()
    if result["valid"]:
        print("Configuration validation passed.")
    else:
        print("Configuration validation failed:")
        for err in result["errors"]:
            print(f" - {err}")
    if result["warnings"]:
        print("Warnings:")
        for warn in result["warnings"]:
            print(f" - {warn}")
    return bool(result["valid"])


def main() -> int:
    """Entry point for environment setup."""
    example = Path(".env.example")
    target = Path(".env")
    existed = ensure_env(example, target)
    if existed and not verify_required_keys(example, target):
        print("Please update the .env file with required values.")
        return 1

    load_dotenv()

    if validate_configuration():
        print("Next steps:")
        print(" 1. Review the .env file and ensure secrets are correct.")
        print(" 2. Start the application with `python start_api.py`.")
        return 0

    print("Please resolve configuration errors before starting the application.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
