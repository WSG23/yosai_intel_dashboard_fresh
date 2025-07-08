import argparse
import re
from pathlib import Path

REPLACEMENTS = {
    "safe_unicode_encode": "safe_encode_text",
    "safe_encode": "safe_encode_text",
    "safe_decode": "safe_decode_bytes",
    "sanitize_unicode_input": "safe_encode_text",
    "sanitize_data_frame": "sanitize_dataframe",
}

METHOD_PATTERNS = {
    r"UnicodeProcessor\.clean_surrogate_chars": "UnicodeProcessor.clean_text",
    r"UnicodeProcessor\.safe_encode_text": "UnicodeProcessor.safe_encode",
    r"UnicodeProcessor\.safe_decode_bytes": "UnicodeProcessor.safe_decode",
}


def migrate_file(path: Path) -> bool:
    text = path.read_text()
    original = text
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    for pattern, repl in METHOD_PATTERNS.items():
        text = re.sub(pattern, repl, text)
    if text != original:
        path.write_text(text)
        return True
    return False


def migrate_directory(directory: Path) -> int:
    changed = 0
    for path in directory.rglob("*.py"):
        if migrate_file(path):
            changed += 1
    return changed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate unicode API migration")
    parser.add_argument("path", nargs="?", default=".", help="directory to process")
    args = parser.parse_args()
    total = migrate_directory(Path(args.path))
    print(f"Updated {total} files")
