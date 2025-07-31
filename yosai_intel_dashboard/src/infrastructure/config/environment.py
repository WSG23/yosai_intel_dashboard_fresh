import os
from pathlib import Path
from typing import Optional


def get_environment() -> str:
    """Return the current environment name."""
    env = os.getenv("YOSAI_ENV", "development").lower()
    if env.startswith("stag"):
        return "staging"
    return env


def select_config_file(explicit_path: Optional[str] = None) -> Optional[Path]:
    """Select the configuration YAML file based on environment variables."""
    if explicit_path:
        return Path(explicit_path)

    env_file = os.getenv("YOSAI_CONFIG_FILE")
    if env_file:
        return Path(env_file)

    env = get_environment()
    config_dir = Path("config")
    env_files = {
        "production": config_dir / "production.yaml",
        "staging": config_dir / "staging.yaml",
        "test": config_dir / "test.yaml",
        "development": config_dir / "config.yaml",
    }
    path = env_files.get(env, config_dir / "config.yaml")
    return path if path.exists() else None
