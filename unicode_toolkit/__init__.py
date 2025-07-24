"""Unified Unicode utilities package."""

from .core import UnicodeProcessor

__all__ = [
    "UnicodeProcessor",
    "UnicodeValidator",
    "UnicodeSanitizer",
    "UnicodeEncoder",
    "UnicodeSQLProcessor",
    "UnicodeQueryHandler",
    "clean_unicode_surrogates",
]


def __getattr__(name: str):
    if name == "UnicodeValidator":
        from importlib import import_module

        return import_module("security.unicode_security_validator").UnicodeSecurityValidator
    if name == "UnicodeSanitizer":
        from core import unicode as _u

        return _u.sanitize_unicode_input
    if name == "UnicodeEncoder":
        from core import unicode as _u

        return _u.UnicodeSQLProcessor
    if name == "UnicodeSQLProcessor":
        from core import unicode as _u

        return _u.UnicodeSQLProcessor
    if name == "UnicodeQueryHandler":
        from config.database_exceptions import UnicodeEncodingError

        class _Handler:
            @staticmethod
            def safe_encode_query(query):
                cleaned = clean_unicode_surrogates(query)
                if cleaned != query:
                    raise UnicodeEncodingError("Invalid Unicode", original_value=query)
                return cleaned

            @staticmethod
            def safe_encode_params(params):
                if params is None:
                    return None
                if isinstance(params, dict):
                    return {k: _Handler.safe_encode_query(v) for k, v in params.items()}
                if isinstance(params, (list, tuple, set)):
                    return type(params)(_Handler.safe_encode_query(v) for v in params)
                return _Handler.safe_encode_query(params)

        return _Handler
    if name == "clean_unicode_surrogates":
        def _clean(text: str, replacement: str = "") -> str:
            if not isinstance(text, str):
                text = str(text)
            out = []
            i = 0
            while i < len(text):
                ch = text[i]
                code = ord(ch)
                if 0xD800 <= code <= 0xDBFF and i + 1 < len(text):
                    next_code = ord(text[i + 1])
                    if 0xDC00 <= next_code <= 0xDFFF:
                        pair = ((code - 0xD800) << 10) + (next_code - 0xDC00) + 0x10000
                        out.append(chr(pair))
                        i += 2
                        continue
                    if replacement:
                        out.append(replacement)
                    i += 1
                    continue
                if 0xDC00 <= code <= 0xDFFF:
                    if replacement:
                        out.append(replacement)
                    i += 1
                    continue
                out.append(ch)
                i += 1
            return "".join(out)

        return _clean
    raise AttributeError(name)

