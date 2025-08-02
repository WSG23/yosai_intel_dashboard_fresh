from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yosai_intel_dashboard.src.core.unicode import clean_unicode_text, safe_encode_text


def main() -> None:
    assert clean_unicode_text("A\ud800B") == "AB"
    assert safe_encode_text("test") == "test"
    print("All checks passed")


if __name__ == "__main__":
    main()
