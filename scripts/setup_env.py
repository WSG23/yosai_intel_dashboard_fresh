#!/usr/bin/env python3
"""Environment setup helper for Yosai Intel Dashboard.

This script ensures a ``.env`` file exists, loads environment variables,
validates configuration via ``ConfigManager`` and prints next steps for
running the application.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from dotenv import load_dotenv

from config import ConfigManager


def create_minimal_env(example: str = ".env.example", target: str = ".env") -> None:
    """Create a minimal ``.env`` file if it doesn't already exist."""
    example_path = Path(example)
    target_path = Path(target)
    if not target_path.exists():
        shutil.copy(example_path, target_path)
        print(
            f"Created {target_path} from {example_path}. Update secret values as needed."
        )
    else:
        print(f"{target_path} already exists; skipping creation.")


def validate_configuration() -> bool:
    """Load and validate configuration, returning ``True`` if valid."""
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


def main() -> None:
    """Entry point for environment setup."""
    create_minimal_env()
    load_dotenv()
    if validate_configuration():
        print("Next steps:")
        print(" 1. Review the generated .env file and fill in required values.")
        print(" 2. Start the application with `python start_api.py`.")
    else:
        print("Please resolve configuration errors before starting the application.")


if __name__ == "__main__":
    main()
