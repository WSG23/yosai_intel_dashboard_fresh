import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.unicode import UnicodeSecurityProcessor, clean_unicode_text, safe_encode_text


def main() -> None:
    assert clean_unicode_text("A\uD800B") == "AB"
    assert safe_encode_text("test") == "test"
    assert UnicodeSecurityProcessor.sanitize_input("<x>") == "&lt;x&gt;"
    print("All checks passed")


if __name__ == "__main__":
    main()
