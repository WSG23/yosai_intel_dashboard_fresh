"""Unicode sanitization utilities."""


def sanitize_unicode_input(input_str: str) -> str:
    """Remove invalid surrogate/control characters and normalize Unicode."""
    try:
        cleaned = input_str.encode("utf-8", errors="ignore").decode("utf-8")
        import unicodedata
        normalized = unicodedata.normalize("NFKC", cleaned)
        allowed = []
        for ch in normalized:
            cat = unicodedata.category(ch)
            if cat.startswith("C") and ch not in "\t\n\r ":
                continue
            allowed.append(ch)
        return "".join(allowed)
    except UnicodeError:
        return input_str.encode("ascii", errors="replace").decode("ascii")

__all__ = ["sanitize_unicode_input"]
