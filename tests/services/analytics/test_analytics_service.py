import time
from typing import Dict, List

import pandas as pd
import pytest
from pydantic import BaseModel

from tests.config import FakeConfiguration  # noqa: F401
from unicode_toolkit.helpers import clean_unicode_surrogates, clean_unicode_text

try:  # pragma: no cover - pydantic v1 fallback
    from pydantic import ConfigDict  # type: ignore
    _EXTRA_CONFIG = {"model_config": ConfigDict(extra="ignore")}
except Exception:  # pragma: no cover
    class _Extra:  # pragma: no cover - pydantic v1 style
        class Config:
            extra = "ignore"

    _EXTRA_CONFIG = {"Config": _Extra.Config}

try:  # pragma: no cover - dependency validation
    from yosai_intel_dashboard.src.services.analytics.analytics_service import AnalyticsService
except Exception:  # pragma: no cover
    pytest.skip("analytics dependencies missing", allow_module_level=True)


class _TopUser(BaseModel):
    user_id: str
    count: int


class _TopDoor(BaseModel):
    door_id: str
    count: int


class _DateRange(BaseModel):
    start: str
    end: str


class _SummarySchema(BaseModel):
    """Minimal schema for summarize_dataframe output."""

    total_events: int
    active_users: int
    active_doors: int
    access_patterns: Dict[str, int]
    date_range: _DateRange
    top_users: List[_TopUser]
    top_doors: List[_TopDoor]

    locals().update(_EXTRA_CONFIG)


def _basic_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_id": ["u1", "u2"],
            "door_id": ["d1", "d2"],
            "access_result": ["Granted", "Denied"],
            "timestamp": ["2024-01-01", "2024-01-02"],
        }
    )


def test_summarize_dataframe_schema_unicode_and_utc():
    service = AnalyticsService()
    summary = service.summarize_dataframe(_basic_df())

    _SummarySchema.model_validate(summary)

    user_id = summary["top_users"][0]["user_id"]
    door_id = summary["top_doors"][0]["door_id"]
    assert clean_unicode_surrogates(user_id) == user_id
    assert clean_unicode_text(door_id) == door_id

    assert summary["date_range"]["start"].endswith("+00:00")
    assert summary["date_range"]["end"].endswith("+00:00")


def test_summarize_dataframe_large_access_patterns():
    service = AnalyticsService()
    n = 5000
    df = pd.DataFrame(
        {
            "person_id": ["u1"] * n,
            "door_id": ["d1"] * n,
            "access_result": [f"R{i}" for i in range(n)],
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
        }
    )

    start = time.perf_counter()
    summary = service.summarize_dataframe(df)
    elapsed = time.perf_counter() - start

    assert summary["total_events"] == n
    assert len(summary["access_patterns"]) == n
    assert elapsed < 5
