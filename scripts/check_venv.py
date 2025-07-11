#!/usr/bin/env python3
"""Check and restore virtual environment if missing."""
import os
import sys
from pathlib import Path

def check_and_restore_venv():
    """Check venv status and restore if needed."""
    project_root = Path.cwd()
    venv_path = project_root / "venv"
    
    # Check if venv exists
    if not venv_path.exists():
        print("❌ Virtual environment missing!")
        print("🔧 Restoring virtual environment...")
        
        # Import and run setup
        sys.path.append(str(project_root / "scripts"))
        from setup_venv import create_venv, install_requirements
        
        if create_venv():
            install_requirements()
            print("✅ Virtual environment restored")
        else:
            print("❌ Failed to restore venv")
            return False
    else:
        print("✅ Virtual environment exists")
    
    # Check if activated
    if os.environ.get('VIRTUAL_ENV'):
        print("✅ Virtual environment is activated")
    else:
        print("⚠️ Virtual environment not activated")
        print("Run: source venv/bin/activate")
    
    return True

if __name__ == "__main__":
    check_and_restore_venv()