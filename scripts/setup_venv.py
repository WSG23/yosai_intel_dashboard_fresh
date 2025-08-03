#!/usr/bin/env python3
"""
Reliable virtual environment setup with backup restore.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_venv(venv_path="venv"):
    """Create virtual environment with error handling."""
    project_root = Path.cwd()
    venv_full_path = project_root / venv_path

    logger.info(f"Creating venv at: {venv_full_path}")

    try:
        # Remove existing if corrupted
        if venv_full_path.exists():
            import shutil

            shutil.rmtree(venv_full_path)

        # Create new venv
        subprocess.run([sys.executable, "-m", "venv", str(venv_full_path)], check=True)

        # Determine activation script
        if os.name == "nt":  # Windows
            activate_script = venv_full_path / "Scripts" / "activate"
            python_exe = venv_full_path / "Scripts" / "python.exe"
        else:  # Unix/Linux/Mac
            activate_script = venv_full_path / "bin" / "activate"
            python_exe = venv_full_path / "bin" / "python"

        logger.info("✅ Virtual environment created")
        logger.info(f"Activate with: source {activate_script}")
        logger.info(f"Python executable: {python_exe}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to create venv: {e}")
        return False


def install_requirements(venv_path="venv"):
    """Install requirements in venv."""
    project_root = Path.cwd()
    requirements_file = project_root / "requirements.txt"

    if not requirements_file.exists():
        logger.info("⚠️ No requirements.txt found")
        return True

    if os.name == "nt":
        pip_exe = project_root / venv_path / "Scripts" / "pip.exe"
    else:
        pip_exe = project_root / venv_path / "bin" / "pip"

    try:
        # Upgrade pip first
        subprocess.run([str(pip_exe), "install", "--upgrade", "pip"], check=True)

        # Install requirements
        subprocess.run(
            [str(pip_exe), "install", "-r", str(requirements_file)], check=True
        )

        logger.info("✅ Requirements installed")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to install requirements: {e}")
        return False


def backup_requirements():
    """Create requirements backup."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            stdout=Path("requirements_backup.txt").open("w", encoding="utf-8"),
            check=True,
        )
        logger.info("✅ Requirements backed up to requirements_backup.txt")
    except Exception as e:
        logger.error(f"⚠️ Could not backup requirements: {e}")


if __name__ == "__main__":
    logger.info("🚀 Setting up virtual environment...")

    backup_requirements()

    if create_venv():
        if install_requirements():
            logger.info("\n🎉 Virtual environment setup complete!")
            logger.info("\nNext steps:")
            logger.info("1. source venv/bin/activate  # (Linux/Mac)")
            logger.info("2. venv\\Scripts\\activate     # (Windows)")
            logger.info("3. python -c 'import dash; print(\"✅ Dash ready\")'")
        else:
            logger.error("\n⚠️ Venv created but requirements failed")
    else:
        logger.error("\n❌ Virtual environment setup failed")
