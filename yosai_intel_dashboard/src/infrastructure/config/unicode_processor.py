from __future__ import annotations

"""Unicode handling helpers built on :class:`core.unicode.UnicodeProcessor`."""

import logging
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

try:  # pragma: no cover - optional security events
    from yosai_intel_dashboard.src.infrastructure.security.events import (
        SecurityEvent,
        emit_security_event,
    )
except Exception:  # pragma: no cover
    from enum import Enum

    class SecurityEvent(Enum):  # type: ignore[override]
        VALIDATION_FAILED = 0

    def emit_security_event(event: SecurityEvent, data: dict | None = None) -> None:
        pass


if TYPE_CHECKING:  # pragma: no cover - imported for type hints only
    from yosai_intel_dashboard.src.core.protocols import UnicodeProcessorProtocol
    from yosai_intel_dashboard.src.core.unicode import (  # noqa: F401
        UnicodeProcessor as _UnicodeProcessor,
    )
    from yosai_intel_dashboard.src.core.unicode import (  # noqa: F401
        contains_surrogates as _contains_surrogates,
    )

logger = logging.getLogger(__name__)


class QueryUnicodeHandler:
    """Sanitize SQL queries and parameters using :class:`UnicodeProcessor`."""

    @staticmethod
    def _encode(value: Any, processor: UnicodeProcessorProtocol) -> Any:
        if isinstance(value, (str, bytes, bytearray)):
            from yosai_intel_dashboard.src.core.unicode import contains_surrogates

            # ``safe_decode_text`` also accepts ``str`` and returns a cleaned str
            text = (
                processor.safe_decode_text(value)
                if isinstance(value, (bytes, bytearray))
                else processor.safe_encode_text(value)
            )
            if contains_surrogates(text):
                emit_security_event(
                    SecurityEvent.VALIDATION_FAILED, {"issue": "surrogate_query"}
                )
                logger.debug("Surrogate characters removed from query value")
            return processor.safe_encode_text(text)
        if isinstance(value, dict):
            return {
                k: QueryUnicodeHandler._encode(v, processor) for k, v in value.items()
            }
        if isinstance(value, (list, tuple, set)):
            return type(value)(QueryUnicodeHandler._encode(v, processor) for v in value)
        return value

    @classmethod
    def handle_unicode_query(
        cls,
        query: str,
        *,
        processor: UnicodeProcessorProtocol | None = None,
        on_surrogate: Callable[[str], None] | None = None,
    ) -> str:
        from yosai_intel_dashboard.src.core.container import get_unicode_processor

        processor = processor or get_unicode_processor()
        from yosai_intel_dashboard.src.core.unicode import contains_surrogates

        if contains_surrogates(query):
            (on_surrogate or logger.debug)("Surrogates detected in query")
        return cls._encode(query, processor)

    @classmethod
    def handle_query_parameters(
        cls,
        params: Any,
        *,
        processor: UnicodeProcessorProtocol | None = None,
        on_surrogate: Callable[[str], None] | None = None,
    ) -> Any:
        from yosai_intel_dashboard.src.core.container import get_unicode_processor

        processor = processor or get_unicode_processor()

        def _cb(text: str) -> None:
            (on_surrogate or logger.debug)("Surrogates detected in query parameters")

        from yosai_intel_dashboard.src.core.unicode import contains_surrogates

        if isinstance(params, str) and contains_surrogates(params):
            _cb(params)
        return cls._encode(params, processor)


class FileUnicodeHandler:
    """Handle filenames and file content safely."""

    @staticmethod
    def handle_file_content(
        content: str | bytes,
        *,
        processor: UnicodeProcessorProtocol | None = None,
        on_surrogate: Callable[[str], None] | None = None,
    ) -> str:
        from yosai_intel_dashboard.src.core.container import get_unicode_processor

        processor = processor or get_unicode_processor()
        text = (
            processor.safe_decode_text(content)
            if isinstance(content, bytes)
            else processor.safe_encode_text(content)
        )
        from yosai_intel_dashboard.src.core.unicode import contains_surrogates

        if contains_surrogates(text):
            (on_surrogate or logger.info)("Surrogates detected in file content")
            emit_security_event(
                SecurityEvent.VALIDATION_FAILED, {"issue": "surrogate_file_content"}
            )
        return processor.safe_encode_text(text)

    @staticmethod
    def handle_filename(
        name: str | Path,
        *,
        processor: UnicodeProcessorProtocol | None = None,
        on_surrogate: Callable[[str], None] | None = None,
    ) -> str:
        from yosai_intel_dashboard.src.core.container import get_unicode_processor

        processor = processor or get_unicode_processor()
        text = str(name)
        from yosai_intel_dashboard.src.core.unicode import contains_surrogates

        if contains_surrogates(text):
            (on_surrogate or logger.info)("Surrogates detected in filename")
            emit_security_event(
                SecurityEvent.VALIDATION_FAILED, {"issue": "surrogate_filename"}
            )
        text = Path(processor.safe_encode_text(text)).name
        return text


class UnicodeSecurityValidator:
    """Validate inputs for Unicode based attacks."""

    @staticmethod
    def validate_input(text: Any) -> str:
        from yosai_intel_dashboard.src.core.container import get_unicode_processor

        processor = get_unicode_processor()
        cleaned = processor.safe_encode_text(text)
        from yosai_intel_dashboard.src.core.unicode import contains_surrogates

        if contains_surrogates(text):
            emit_security_event(
                SecurityEvent.VALIDATION_FAILED, {"issue": "surrogate_input"}
            )
            logger.info("Surrogate characters removed from input")
        return cleaned

    @staticmethod
    def check_for_attacks(text: Any) -> bool:
        sanitized = UnicodeSecurityValidator.validate_input(text)
        try:
            normalised = unicodedata.normalize("NFKC", sanitized)
        except Exception:  # pragma: no cover - best effort
            normalised = sanitized
        # homograph detection: if NFKC changes the string significantly
        return normalised != sanitized


def encode_query(
    query: str | bytes,
    *,
    processor: "UnicodeProcessorProtocol" | None = None,
    on_surrogate: Callable[[str], None] | None = None,
) -> str:
    """Public wrapper for :class:`QueryUnicodeHandler` query encoding.

    Parameters
    ----------
    query:
        The SQL query to sanitise.  ``bytes`` inputs are decoded using the
        provided processor.
    processor:
        Optional processor instance.  Falls back to the global container if
        omitted.
    on_surrogate:
        Optional callback invoked when surrogate code points are detected.
    """

    return QueryUnicodeHandler.handle_unicode_query(
        query, processor=processor, on_surrogate=on_surrogate
    )


def encode_params(
    params: Any,
    *,
    processor: "UnicodeProcessorProtocol" | None = None,
    on_surrogate: Callable[[str], None] | None = None,
) -> Any:
    """Recursively encode SQL parameters.

    Non-string objects are returned unchanged. ``bytes`` are decoded using the
    processor and nested containers are traversed.
    """

    return QueryUnicodeHandler.handle_query_parameters(
        params, processor=processor, on_surrogate=on_surrogate
    )


__all__ = [
    "QueryUnicodeHandler",
    "FileUnicodeHandler",
    "UnicodeSecurityValidator",
    "encode_query",
    "encode_params",
]
