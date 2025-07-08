from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.unicode import clean_unicode_text, safe_encode_text, UnicodeSecurityProcessor


def main() -> None:
    assert clean_unicode_text("A\uD800B") == "AB"
    assert safe_encode_text("test") == "test"
    assert UnicodeSecurityProcessor.sanitize_input("<x>") == "&lt;x&gt;"
    print("All checks passed")


if __name__ == "__main__":
    main()
