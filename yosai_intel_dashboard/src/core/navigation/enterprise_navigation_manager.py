from __future__ import annotations

"""Navigation state management with loop detection."""

from collections import deque
from typing import Deque, List


class NavigationLoopError(Exception):
    """Raised when a navigation loop is detected."""


class EnterpriseNavigationManager:
    """Track navigation history and detect loops."""

    def __init__(self, max_history: int = 50, loop_threshold: int = 5) -> None:
        self.history: Deque[str] = deque(maxlen=max_history)
        self.loop_threshold = loop_threshold

    # ------------------------------------------------------------------
    def record_navigation(self, page: str) -> None:
        """Record navigation to ``page`` and check for loops."""
        self.history.append(page)
        if self._check_loop(page):
            raise NavigationLoopError(f"Navigation loop detected on {page}")

    # ------------------------------------------------------------------
    def _check_loop(self, page: str) -> bool:
        count = 0
        for entry in reversed(self.history):
            if entry != page:
                break
            count += 1
        return count >= self.loop_threshold

    # ------------------------------------------------------------------
    def get_history(self) -> List[str]:
        """Return list of visited pages."""
        return list(self.history)

    # ------------------------------------------------------------------
    def clear(self) -> None:
        """Clear stored navigation history."""
        self.history.clear()
