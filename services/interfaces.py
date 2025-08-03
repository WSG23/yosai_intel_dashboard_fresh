"""Protocol definitions for service adapters used in tests."""

from __future__ import annotations

from typing import Protocol, Any


class AnalyticsServiceProtocol(Protocol):
    """Minimal protocol for analytics adapters."""

    async def get_dashboard_summary_async(self) -> Any: ...
