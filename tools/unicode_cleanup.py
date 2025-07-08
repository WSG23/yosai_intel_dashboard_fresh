"""Utilities for final Unicode cleanup."""

import json
import re
import subprocess
import sys
from pathlib import Path

from typing import Dict, List, Tuple

import chardet

def safe_read_text(file_path):
    """Direct replacement for pathlib.Path.read_text() with encoding detection."""
    path = Path(file_path)
    raw_bytes = path.read_bytes()
    
    # Try chardet detection first if available
    try:
        detected = chardet.detect(raw_bytes)
        detected_encoding = detected.get('encoding') if detected else None
        
        if detected_encoding:
            try:
                return raw_bytes.decode(detected_encoding)
            except (UnicodeDecodeError, LookupError):
                pass
    except:
        pass
    
    # Try common encodings
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            return raw_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    
    # Final fallback
    return raw_bytes.decode('utf-8', errors='replace')




# ----------------------------------------------------------------------
# A. Legacy Reference Scanner
# ----------------------------------------------------------------------
def scan_legacy_references(base_dir: str = ".") -> Dict[str, List[Tuple[str, int]]]:
    """Find references to the deprecated ``core.unicode_processor`` module."""
    patterns = {
        "from_import": re.compile(r"^\s*from\s+core\.unicode_processor\s+import", re.M),
        "import_module": re.compile(r"^\s*import\s+core\.unicode_processor(\s+as\s+\w+)?", re.M),
        "attribute_access": re.compile(r"\bcore\.unicode_processor\."),
        "legacy_handler": re.compile(
            r"services\.upload\.utils\.unicode_handler\.safe_unicode_encode"
        ),
    }

    found: Dict[str, List[Tuple[str, int]]] = {}
    for path in Path(base_dir).rglob("*.py"):
        text = safe_read_text(path)
        matches: List[Tuple[str, int]] = []
        for key, pattern in patterns.items():
            for m in pattern.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                matches.append((key, line))
        if matches:
            found[str(path)] = matches
    return found


# ----------------------------------------------------------------------
# B. Automated Import Updater
# ----------------------------------------------------------------------
def update_imports(base_dir: str = ".") -> Dict[str, int]:
    """Update references to ``core.unicode_processor`` to ``core.unicode``."""
    replacements = {
        re.compile(r"from\s+core\.unicode_processor\s+import"): "from core.unicode import",
        re.compile(r"import\s+core\.unicode_processor(\s+as\s+)"): r"import core.unicode\1",
        re.compile(r"import\s+core\.unicode_processor\b"): "import core.unicode",
        re.compile(r"\bcore\.unicode_processor\."): "core.unicode.",
        re.compile(
            r"services\.upload\.utils\.unicode_handler\.safe_unicode_encode"
        ): "core.unicode.safe_encode_text",
    }

    modified: Dict[str, int] = {}
    for path in Path(base_dir).rglob("*.py"):
        text = safe_read_text(path)
        original = text
        count = 0
        for pattern, repl in replacements.items():
            text, n = pattern.subn(repl, text)
            count += n
        if text != original:
            path.write_text(text, encoding="utf-8")
            modified[str(path)] = count
    return modified


# ----------------------------------------------------------------------
# C. Removal Safety Validator
# ----------------------------------------------------------------------
def validate_removal(base_dir: str = ".") -> Tuple[bool, str]:
    """Run checks ensuring removal of the deprecated files is safe."""
    remaining = scan_legacy_references(base_dir)
    if remaining:
        return False, "Legacy references remain: " + json.dumps(remaining, indent=2)

    if Path("core/unicode_processor.py").exists():
        print("core/unicode_processor.py still present but no references found.")

    proc = subprocess.run(
        [sys.executable, "tools/validate_unicode_cleanup.py"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return False, proc.stdout + proc.stderr

    return True, proc.stdout


# ----------------------------------------------------------------------
# D. Complete Cleanup Function
# ----------------------------------------------------------------------
def complete_unicode_cleanup(base_dir: str = ".", dry_run: bool = False) -> Dict[str, object]:
    """Perform the entire cleanup procedure."""
    base = Path(base_dir)
    all_py = list(base.rglob("*.py"))

    references = scan_legacy_references(base_dir)
    report = {
        "files_scanned": len(all_py),
        "imports_updated": 0,
        "files_removed": [],
        "validation_passed": False,
    }

    if dry_run:
        print(json.dumps(references, indent=2))
        return report

    if references:
        updated = update_imports(base_dir)
        report["imports_updated"] = sum(updated.values())

    remaining = scan_legacy_references(base_dir)
    if remaining:
        raise RuntimeError("Unresolved references remain: " + json.dumps(remaining, indent=2))

    removable = [
        Path("core/unicode_processor.py"),
        Path("tools/migration_validator.py"),
        Path("tools/legacy_unicode_audit.py"),
        Path("scripts/unicode_migration.py"),
    ]
    for path in removable:
        if path.exists():
            path.unlink()
            report["files_removed"].append(str(path))

    ok, out = validate_removal(base_dir)
    report["validation_passed"] = ok
    if not ok:
        raise RuntimeError("Validation failed:\n" + out)

    return report


# ----------------------------------------------------------------------
# E. Validation Confirmation
# ----------------------------------------------------------------------
def confirm_cleanup() -> None:
    """Simple functional test after cleanup."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("error", DeprecationWarning)
        from core.unicode import (
            clean_unicode_text,
            safe_decode_bytes,
            safe_encode_text,
            sanitize_dataframe,
        )

    assert not w, "Deprecation warnings detected"

    assert clean_unicode_text("A\uD800") == "A"
    assert safe_encode_text("test") == "test"
    assert safe_decode_bytes(b"x") == "x"

    import pandas as pd

    df = pd.DataFrame({"=bad": ["A\uD800"]})
    cleaned = sanitize_dataframe(df)
    assert list(cleaned.columns) == ["bad"]
    assert cleaned.iloc[0, 0] == "A"

    print("Unicode cleanup validated successfully.")


if __name__ == "__main__":
    result = complete_unicode_cleanup()
    print(json.dumps(result, indent=2))
    confirm_cleanup()
