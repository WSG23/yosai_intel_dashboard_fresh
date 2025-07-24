from __future__ import annotations

"""Python error boundary helper.

Deprecated: use the React component in ``src/components/shared/ErrorBoundary.tsx``.
"""

import logging
from typing import Any, Callable

from dash import html

logger = logging.getLogger(__name__)


class ErrorBoundary:
    """Decorate functions with error handling returning fallback UI."""

    def __init__(self, fallback: Callable[[Exception], Any] | None = None) -> None:
        self.fallback = fallback or (
            lambda _exc: html.Div(
                "An unexpected error occurred.", className="alert alert-danger"
            )
        )

    # ------------------------------------------------------------------
    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # pragma: no cover - dev helper
                logger.exception("ErrorBoundary captured: %s", exc)
                return self.fallback(exc)

        return wrapper
