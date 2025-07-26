#!/usr/bin/env python3
"""
Quick diagnostic tool to check project structure
"""

import os
import sys
from pathlib import Path
from collections import Counter


def check_project_structure(path="."):
    """Analyze project structure and file types"""
    project_path = Path(path)

    print(f"\n🔍 Analyzing: {project_path.absolute()}")
    print("=" * 60)

    # Check if path exists
    if not project_path.exists():
        print(f"❌ Error: Path '{project_path}' does not exist!")
        return

    # Count file types
    file_extensions = Counter()
    python_files = []
    directories = []

    for item in project_path.rglob("*"):
        if item.is_file():
            ext = item.suffix.lower()
            file_extensions[ext] += 1
            if ext == ".py":
                python_files.append(item)
        elif item.is_dir() and not any(part.startswith(".") for part in item.parts):
            directories.append(item)

    # Print summary
    print(f"\n📁 Directory Structure:")
    print(f"   Total directories: {len(directories)}")

    # Show top-level directories
    top_dirs = [d for d in directories if d.parent == project_path]
    if top_dirs:
        print(f"\n   Top-level directories:")
        for d in sorted(top_dirs)[:10]:
            print(f"      - {d.name}/")

    print(f"\n📄 File Summary:")
    print(f"   Total files: {sum(file_extensions.values())}")

    print(f"\n   File types found:")
    for ext, count in file_extensions.most_common(10):
        if ext:
            print(f"      {ext}: {count} files")
        else:
            print(f"      (no extension): {count} files")

    print(f"\n🐍 Python Files: {len(python_files)}")
    if python_files:
        print("\n   Sample Python files:")
        for py_file in sorted(python_files)[:10]:
            rel_path = py_file.relative_to(project_path)
            size = py_file.stat().st_size
            print(f"      - {rel_path} ({size:,} bytes)")

        if len(python_files) > 10:
            print(f"      ... and {len(python_files) - 10} more")

    # Check for common project files
    print(f"\n📋 Project Files:")
    common_files = [
        "requirements.txt",
        "setup.py",
        "README.md",
        "Dockerfile",
        ".gitignore",
        "Makefile",
        "pyproject.toml",
    ]

    for fname in common_files:
        fpath = project_path / fname
        if fpath.exists():
            print(f"   ✓ {fname}")
        else:
            print(f"   ✗ {fname} (not found)")

    # Check for potential issues
    print(f"\n⚠️  Potential Issues:")
    issues = []

    if len(python_files) == 0:
        issues.append("No Python files found - check if you're in the right directory")

    if (
        not (project_path / "__init__.py").exists()
        and not (project_path / "setup.py").exists()
    ):
        issues.append(
            "No __init__.py or setup.py found in root - may not be a Python package"
        )

    git_dir = project_path / ".git"
    if not git_dir.exists():
        issues.append(
            "No .git directory found - project may not be under version control"
        )

    if issues:
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("   ✓ None detected")

    print("\n" + "=" * 60)
    print(f"✅ Analysis complete for: {project_path.absolute()}")

    return len(python_files) > 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "."

    has_python = check_project_structure(path)

    if has_python:
        print(f"\n💡 Ready to run code analyzer!")
        print(f"   Run: python3 -m analysis.unified_analyzer {Path(path).absolute()}")
    else:
        print(f"\n❌ No Python files found. Please check:")
        print(f"   1. You're in the correct directory")
        print(f"   2. The project contains .py files")
        print(f"   3. Try running from the parent directory")
