#!/usr/bin/env python3
"""Utility to remove runtime patch files used during migration."""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

PATCH_FILES = [
    Path("tools/step2_add_missing_methods.py"),
    Path("tools/step2_final_fix.py"),
    Path("tools/test_analytics_both_fixes.py"),
    Path("tools/apply_callback_patch.py"),
]

EXPECTED_UPLOAD_METHODS = [
    "analyze_uploaded_data",
    "load_uploaded_data",
    "get_analytics_from_uploaded_data",
    "clean_uploaded_dataframe",
    "summarize_dataframe",
    "_load_data",
    "_validate_data",
    "_calculate_statistics",
    "_process_uploaded_data_directly",
    "_format_results",
]
CALLBACK_ATTRS = ["callback", "unified_callback"]
TEST_CMD = [
    "pytest",
    "tests/test_upload_processing_module.py",
    "tests/test_callback_manager_events.py",
    "-q",
]

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def verify_imports() -> list[str]:
    errors: list[str] = []
    print(" - Checking UploadAnalyticsProcessor")
    try:
        module = __import__(
            "src.services.analytics.upload_analytics", fromlist=["UploadAnalyticsProcessor"]
        )
        UploadAnalyticsProcessor = getattr(module, "UploadAnalyticsProcessor")
        missing = [m for m in EXPECTED_UPLOAD_METHODS if not hasattr(UploadAnalyticsProcessor, m)]
        if missing:
            errors.append("UploadAnalyticsProcessor missing: " + ", ".join(missing))
    except Exception as exc:  # pragma: no cover - defensive
        errors.append(f"UploadAnalyticsProcessor import error: {exc}")

    print(" - Checking TrulyUnifiedCallbacks")
    try:
        module = __import__(
            "src.infrastructure.callbacks.unified_callbacks", fromlist=["TrulyUnifiedCallbacks"]
        )
        TrulyUnifiedCallbacks = getattr(module, "TrulyUnifiedCallbacks")
        for attr in CALLBACK_ATTRS:
            if not hasattr(TrulyUnifiedCallbacks, attr):
                errors.append(f"TrulyUnifiedCallbacks missing attribute: {attr}")
    except Exception as exc:  # pragma: no cover - defensive
        errors.append(f"TrulyUnifiedCallbacks import error: {exc}")

    if errors:
        for err in errors:
            print(f"   ERROR: {err}")
    else:
        print("   Import checks passed.")
    return errors


def run_tests() -> list[str]:
    print(" - Running smoke tests")
    proc = subprocess.run(TEST_CMD, cwd=ROOT, capture_output=True, text=True)
    print(proc.stdout, end="")
    if proc.returncode != 0:
        return [f"Tests exited with {proc.returncode}"]
    return []


def backup(files: list[Path], dry_run: bool) -> tuple[list[Path], Path | None]:
    if dry_run:
        print("Dry run: skipping backup.")
        return [], None
    timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_dir = ROOT / "tools" / "runtime_patch_backups" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    backed_up: list[Path] = []
    for file in files:
        if file.exists():
            dest = backup_dir / file.name
            shutil.copy2(file, dest)
            backed_up.append(file)
            print(f"Backed up {file} -> {dest}")
        else:
            print(f"Patch file {file} not found for backup.")
    return backed_up, backup_dir


def remove(files: list[Path], dry_run: bool) -> list[Path]:
    removed: list[Path] = []
    for file in files:
        if file.exists():
            if dry_run:
                print(f"Dry run: would remove {file}")
                removed.append(file)
            else:
                file.unlink()
                removed.append(file)
                print(f"Removed {file}")
        else:
            print(f"Patch file {file} not found; nothing to remove.")
    return removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remove runtime patch files")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without modifying files")
    parser.add_argument("--no-backup", action="store_true", help="Do not create backups")
    parser.add_argument("--skip-verify", action="store_true", help="Skip running smoke tests")
    args = parser.parse_args(argv)

    print("Pre-removal verification:")
    errors = verify_imports()
    if not args.skip_verify:
        errors.extend(run_tests())
    else:
        print(" - Skipping smoke tests")
    if errors:
        print("Aborting due to pre-removal errors.")
        return 1

    backed_up: list[Path] = []
    backup_dir: Path | None = None
    if not args.no_backup:
        print("Backing up patch files...")
        backed_up, backup_dir = backup(PATCH_FILES, args.dry_run)
    else:
        print("Skipping backup as requested.")

    print("Removing patch files...")
    removed = remove(PATCH_FILES, args.dry_run)

    print("\nPost-removal verification:")
    post_errors = verify_imports()
    if not args.skip_verify:
        post_errors.extend(run_tests())
    else:
        print(" - Skipping smoke tests")

    print("\nSummary:")
    if backed_up:
        print(f" Backed up {len(backed_up)} file(s) to {backup_dir}")
    else:
        print(" No files backed up")
    if removed:
        if args.dry_run:
            print(f" Would remove {len(removed)} file(s)")
        else:
            print(f" Removed {len(removed)} file(s)")
    else:
        print(" No files removed")

    if post_errors:
        print("Post-removal verification failed:")
        for err in post_errors:
            print(f" - {err}")
        return 1
    print("Post-removal verification succeeded.")
    print("All operations completed successfully.")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry
    raise SystemExit(main())
