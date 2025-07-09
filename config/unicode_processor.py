from __future__ import annotations

"""Unicode sanitization helpers used by configuration utilities."""

import logging
import os
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable, List, Protocol

logger = logging.getLogger(__name__)


class UnicodeProcessorProtocol(Protocol):
    """Protocol for Unicode processing utilities."""

    def sanitize_query(self, query: str) -> str:
        """Return ``query`` cleaned for safe SQL execution."""

    def sanitize_filename(self, filename: str) -> str:
        """Return a safe filename stripped of unsafe characters."""

    def sanitize_content(self, content: str) -> str:
        """Return ``content`` cleaned of surrogates and controls."""

    def process_with_details(self, text: str) -> "UnicodeProcessingResult":
        """Return detailed processing information for ``text``."""

    def validate_encoding(self, text: str, encoding: str = "utf-8") -> bool:
        """Return ``True`` if ``text`` encodes with ``encoding``."""

    def batch_process(self, items: Iterable[str]) -> List[str]:
        """Return list of sanitized strings from ``items``."""

    def register_callback(self, hook: str, callback: Callable[..., None]) -> None:
        """Register a ``callback`` for the given ``hook``."""


class SanitizationStrategy(Enum):
    """Behaviour when encountering problematic characters."""

    STRICT = "strict"
    REPLACE = "replace"
    IGNORE = "ignore"


@dataclass
class UnicodeProcessingResult:
    """Result of a unicode sanitization operation."""

    original: str
    sanitized: str
    surrogates_removed: int
    encoding_valid: bool


class UnicodeProcessor(UnicodeProcessorProtocol):
    """Implementation of :class:`UnicodeProcessorProtocol`."""

    _SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")
    _CONTROL_RE = re.compile(r"[\x00-\x1F\x7F]")
    _INVALID_NAME_RE = re.compile(r"[\\/:*?\"<>|]")

    def __init__(self) -> None:
        self._callbacks: dict[str, List[Callable[..., None]]] = {
            "pre_processing": [],
            "post_processing": [],
            "error_handling": [],
            "surrogate_detected": [],
        }

    # ------------------------------------------------------------------
    # Callback registration helpers
    # ------------------------------------------------------------------
    def register_callback(self, hook: str, callback: Callable[..., None]) -> None:
        """Register ``callback`` for a specific ``hook``."""
        if hook not in self._callbacks:
            raise ValueError(f"Unknown callback hook: {hook}")
        self._callbacks[hook].append(callback)

    def _run_callbacks(self, hook: str, *args: Any) -> None:
        for cb in self._callbacks.get(hook, []):
            try:
                cb(*args)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Callback %s failed: %s", hook, exc)

    # ------------------------------------------------------------------
    def _replace_surrogate(
        self, match: re.Match[str], strategy: SanitizationStrategy
    ) -> str:
        self._run_callbacks("surrogate_detected", match.group(0))
        if strategy is SanitizationStrategy.REPLACE:
            return "\ufffd"
        if strategy is SanitizationStrategy.IGNORE:
            return match.group(0)
        return ""

    def validate_encoding(self, text: str, encoding: str = "utf-8") -> bool:
        """Return ``True`` if ``text`` can be encoded with ``encoding``."""
        try:
            text.encode(encoding)
            return True
        except UnicodeEncodeError as exc:  # pragma: no cover - logging only
            logger.error("Encoding validation failed: %s", exc)
            self._run_callbacks("error_handling", exc)
            return False

    # ------------------------------------------------------------------
    def process_with_details(
        self, text: str, strategy: SanitizationStrategy = SanitizationStrategy.STRICT
    ) -> UnicodeProcessingResult:
        """Return sanitized text with detailed metrics."""
        self._run_callbacks("pre_processing", text)
        if not isinstance(text, str):
            text = str(text)
        try:
            text = unicodedata.normalize("NFKC", text)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Unicode normalization failed: %s", exc)
            self._run_callbacks("error_handling", exc)
        count = 0

        def replacer(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return self._replace_surrogate(match, strategy)

        cleaned = self._SURROGATE_RE.sub(replacer, text)
        cleaned = self._CONTROL_RE.sub("", cleaned)
        valid = self.validate_encoding(cleaned)
        result = UnicodeProcessingResult(text, cleaned, count, valid)
        self._run_callbacks("post_processing", result)
        return result

    def sanitize_content(
        self, content: str, strategy: SanitizationStrategy = SanitizationStrategy.STRICT
    ) -> str:
        """Return ``content`` sanitised according to ``strategy``."""
        return self.process_with_details(content, strategy).sanitized

    def sanitize_query(
        self, query: str, strategy: SanitizationStrategy = SanitizationStrategy.STRICT
    ) -> str:
        """Return ``query`` sanitised for SQL execution."""
        result = self.sanitize_content(query, strategy)
        try:
            data = result.encode("utf-8", "surrogateescape")
            result = data.decode("utf-8", "replace")
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Query sanitization failed: %s", exc)
            self._run_callbacks("error_handling", exc)
        return result

    def sanitize_filename(
        self,
        filename: str,
        strategy: SanitizationStrategy = SanitizationStrategy.STRICT,
    ) -> str:
        """Return a safe version of ``filename``."""
        cleaned = self.sanitize_content(filename, strategy)
        cleaned = os.path.basename(cleaned)
        cleaned = cleaned.strip()
        cleaned = self._INVALID_NAME_RE.sub("_", cleaned)
        return cleaned or "file"

    def batch_process(
        self,
        items: Iterable[str],
        strategy: SanitizationStrategy = SanitizationStrategy.STRICT,
    ) -> List[str]:
        """Sanitize a batch of strings."""
        return [self.sanitize_content(i, strategy) for i in items]


__all__ = [
    "UnicodeProcessorProtocol",
    "SanitizationStrategy",
    "UnicodeProcessingResult",
    "UnicodeProcessor",
]
