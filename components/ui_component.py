from __future__ import annotations

"""Base UI component with DI and Unicode helpers."""

from typing import Any, Optional

from core.container import container as _global_container
from core.protocols import ServiceContainer, UnicodeProcessorProtocol, get_unicode_processor
from core.unicode import sanitize_unicode_input


class UIComponent:
    """Base class for UI components with DI and Unicode helpers."""

    def __init__(
        self,
        *,
        container: Optional[ServiceContainer] = None,
        unicode_processor: Optional[UnicodeProcessorProtocol] = None,
    ) -> None:
        self.container = container or _global_container
        self.unicode_processor = unicode_processor or get_unicode_processor(self.container)

    # ------------------------------------------------------------------
    def sanitize(self, text: Any) -> str:
        """Return ``text`` sanitized for safe display."""
        try:
            return sanitize_unicode_input(text)
        except Exception:
            return str(text)

    # ------------------------------------------------------------------
    def layout(self) -> Any:  # pragma: no cover - interface
        raise NotImplementedError

    # ------------------------------------------------------------------
    def register_callbacks(self, manager: Any, controller: Any | None = None) -> None:  # pragma: no cover - interface
        return None


__all__ = ["UIComponent"]
