from __future__ import annotations

"""Pydantic models for analytics service I/O."""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .unicode import normalize_text


class AnalyticsQueryV1(BaseModel):
    """Input model for analytics queries."""

    source: str = Field(..., description="Analytics data source")

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("source")
    @classmethod
    def _normalize_source(cls, value: str) -> str:
        normalized = normalize_text(value).strip().lower()
        if normalized not in {"sample", "uploaded", "database"}:
            raise ValueError(
                "source must be one of: sample, uploaded, database",
            )
        return normalized


class DateRange(BaseModel):
    """Date range with UTC coercion."""

    start: datetime
    end: datetime

    model_config = ConfigDict(extra="forbid")

    @field_validator("start", "end", mode="before")
    @classmethod
    def _coerce_utc(cls, value: datetime) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class PatternSummary(BaseModel):
    """Summary of a detected pattern."""

    pattern: str
    count: int


class DeviceDistribution(BaseModel):
    """Distribution of events across devices."""

    device_id: str
    count: int


class AnalyticsSummaryV1(BaseModel):
    """Output model for analytics summaries."""

    status: str
    message: Optional[str] = None
    total_rows: Optional[int] = None
    patterns: List[PatternSummary] = Field(default_factory=list)
    device_distribution: List[DeviceDistribution] = Field(default_factory=list)
    date_range: Optional[DateRange] = None

    model_config = ConfigDict(extra="allow")


__all__ = [
    "AnalyticsQueryV1",
    "AnalyticsSummaryV1",
    "PatternSummary",
    "DeviceDistribution",
    "DateRange",
]
