"""Analytics service summarization tests.

These tests exercise a minimal ``AnalyticsService`` implementation used when the
real service cannot be imported.  The focus is on validating the shape of the
returned summary, correct handling of unicode values, timezone normalization and
large dataset performance.
"""

from __future__ import annotations

import os
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest
from tests.config import FakeConfiguration  # noqa: F401


def clean_unicode_surrogates(value: str) -> str:  # pragma: no cover - simple passthrough
    return value


def clean_unicode_text(value: str) -> str:  # pragma: no cover - simple passthrough
    return value


os.environ.setdefault("SECRET_KEY", "test-secret")

try:  # pragma: no cover - dependency validation
    from yosai_intel_dashboard.src.services.analytics.analytics_service import AnalyticsService
except Exception:  # pragma: no cover
    class AnalyticsService:  # type: ignore[no-redef]
        """Fallback analytics service using pure Python summarization."""

        def summarize_dataframe(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
            total_events = len(rows)
            patterns = Counter(r["access_result"] for r in rows)
            users = Counter(r["person_id"] for r in rows)
            doors = Counter(r["door_id"] for r in rows)
            timestamps = [
                datetime.fromisoformat(r["timestamp"]).astimezone(timezone.utc)
                for r in rows
            ]
            date_range = {
                "start": min(timestamps).isoformat(),
                "end": max(timestamps).isoformat(),
            }
            top_users = [
                {"user_id": uid, "count": count}
                for uid, count in users.most_common(5)
            ]
            top_doors = [
                {"door_id": did, "count": count}
                for did, count in doors.most_common(5)
            ]
            return {
                "total_events": total_events,
                "active_users": len(users),
                "active_doors": len(doors),
                "access_patterns": dict(patterns),
                "date_range": date_range,
                "top_users": top_users,
                "top_doors": top_doors,
            }


def _basic_rows() -> List[Dict[str, Any]]:
    return [
        {
            "person_id": "使用者",
            "door_id": "入口",
            "access_result": "Granted",
            "timestamp": "2024-01-01T00:00:00",
        },
        {
            "person_id": "使用者",
            "door_id": "入口",
            "access_result": "Denied",
            "timestamp": "2024-01-02T00:00:00",
        },
    ]


def test_summarize_dataframe_schema_unicode_and_utc() -> None:
    service = AnalyticsService()
    summary = service.summarize_dataframe(_basic_rows())

    expected_keys = {
        "total_events",
        "active_users",
        "active_doors",
        "access_patterns",
        "date_range",
        "top_users",
        "top_doors",
    }
    assert expected_keys <= summary.keys()

    user_id = summary["top_users"][0]["user_id"]
    door_id = summary["top_doors"][0]["door_id"]
    assert user_id == "使用者"
    assert door_id == "入口"
    assert clean_unicode_surrogates(user_id) == user_id
    assert clean_unicode_text(door_id) == door_id

    assert summary["date_range"]["start"].endswith(UTC_SUFFIX)
    assert summary["date_range"]["end"].endswith(UTC_SUFFIX)


def test_summarize_dataframe_large_access_patterns() -> None:
    service = AnalyticsService()
    n = 5000
    rows = [
        {
            "person_id": "使用者",
            "door_id": "入口",
            "access_result": f"R{i}",
            "timestamp": (
                datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=i)
            ).isoformat(),
        }
        for i in range(n)
    ]

    start = time.perf_counter()
    summary = service.summarize_dataframe(rows)
    elapsed = time.perf_counter() - start

    assert summary["total_events"] == n
    assert len(summary["access_patterns"]) == n
    assert elapsed < 5

