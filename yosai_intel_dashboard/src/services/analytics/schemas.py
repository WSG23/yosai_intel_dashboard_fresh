from __future__ import annotations

"""Pydantic models for analytics service I/O."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalyticsQueryV1(BaseModel):
    """Input model for analytics queries."""

    source: str = Field(..., description="Analytics data source")

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("source")
    @classmethod
    def _normalize_source(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"sample", "uploaded", "database"}:
            raise ValueError(
                "source must be one of: sample, uploaded, database"
            )
        return normalized


class AnalyticsSummaryV1(BaseModel):
    """Output model for analytics summaries."""

    status: str
    message: Optional[str] = None
    total_rows: Optional[int] = None

    model_config = ConfigDict(extra="allow")
