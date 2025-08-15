"""Pydantic models shared between analytics services."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel

from yosai_intel_dashboard.src.services.intel_analysis_service.core import (
    AccessRecord,
    Interaction,
    TrustLink,
)


class ReportRequest(BaseModel):
    """Parameters for report generation."""

    type: str
    timeframe: str | None = None
    format: str | None = "json"
    params: Dict[str, Any] | None = None


class SocialNetworkRequest(BaseModel):
    """Interaction data for social network analysis."""

    interactions: list[Interaction]
    min_occurrences: int = 3


class AccessLogRequest(BaseModel):
    """Access log for behavioural clique analysis."""

    records: list[AccessRecord]


class RiskPropagationRequest(BaseModel):
    """Parameters for risk propagation analysis."""

    base_risks: Dict[str, float]
    links: list[TrustLink]
    iterations: int = 1
    decay: float = 0.5
