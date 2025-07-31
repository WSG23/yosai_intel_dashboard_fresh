"""Metadata Enhancement Engine.

This module defines :class:`MetadataEnhancementEngine`, a lightweight
service that coordinates several analysis subcomponents. The engine is
constructed through the dependency injection container and relies on the
existing upload and analytics services.

The public API consists of a single :meth:`enhance_metadata` method which
loads uploaded data via :class:`UploadDataServiceProtocol` and returns a
dictionary summarizing results from each subcomponent as well as the
analytics service dashboard summary.

Expected input is the same set of DataFrame structures produced by the
upload subsystem. Each DataFrame should include ``person_id``, ``door_id``,
``timestamp`` and ``access_result`` columns. The combined output has the
form::

    {
        "behavior": {"unique_users": int, "unique_doors": int, "events": int},
        "security": {"denied_rate": float},
        "patterns": {"common_paths": List[Dict[str, Any]]},
        "temporal": {"first_event": str | None, "last_event": str | None},
        "compliance": {"compliant": bool, "missing_columns": List[str]},
        "analytics": Dict[str, Any],
    }
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol, runtime_checkable

try:
    from typing import override
except ImportError:  # pragma: no cover - for Python <3.12

    from typing_extensions import override

import pandas as pd

from core.di_decorators import inject, injectable
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from yosai_intel_dashboard.src.services.analytics.protocols import AnalyticsServiceProtocol
from yosai_intel_dashboard.src.services.upload.protocols import UploadDataServiceProtocol


@runtime_checkable
class MetadataEnhancementProtocol(Protocol):
    """Protocol for metadata enhancement engines."""

    def enhance_metadata(self) -> Dict[str, Any]:
        """Run all enhancement stages and return aggregated results."""
        ...


@dataclass
class BehaviorAnalyzer:
    """Compute basic behavioral metrics."""

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {"unique_users": 0, "unique_doors": 0, "events": 0}
        users = df["person_id"].nunique() if "person_id" in df else 0
        doors = df["door_id"].nunique() if "door_id" in df else 0
        return {"unique_users": users, "unique_doors": doors, "events": len(df)}


@dataclass
class SecurityRefiner:
    """Calculate simple security statistics."""

    def refine(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "access_result" not in df:
            return {"denied_rate": 0.0}
        total = len(df)
        denied = (df["access_result"].str.lower() == "denied").sum()
        return {"denied_rate": denied / total if total else 0.0}


@dataclass
class PatternLearner:
    """Identify frequently occurring user/door combinations."""

    def learn(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or not {"person_id", "door_id"}.issubset(df.columns):
            return {"common_paths": []}
        paths = df.groupby(["person_id", "door_id"]).size().reset_index(name="count")
        top = paths.sort_values("count", ascending=False).head(3)
        return {"common_paths": top.to_dict("records")}


@dataclass
class TemporalAnalyzer:
    """Extract temporal ranges from the data."""

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "timestamp" not in df:
            return {"first_event": None, "last_event": None}
        first = df["timestamp"].min()
        last = df["timestamp"].max()
        return {"first_event": str(first), "last_event": str(last)}


@dataclass
class ComplianceChecker:
    """Validate presence of required columns."""

    required: List[str] = None

    def __post_init__(self) -> None:
        if self.required is None:
            self.required = ["person_id", "door_id", "timestamp", "access_result"]

    def check(self, df: pd.DataFrame) -> Dict[str, Any]:
        missing = [c for c in self.required if c not in df.columns]
        return {"compliant": not missing, "missing_columns": missing}


@injectable
class MetadataEnhancementEngine(MetadataEnhancementProtocol):
    """Orchestrates metadata enhancement subcomponents."""

    @inject
    def __init__(
        self,
        upload_data_service: UploadDataServiceProtocol,
        analytics_service: AnalyticsServiceProtocol,
        behavior_analyzer: BehaviorAnalyzer,
        security_refiner: SecurityRefiner,
        pattern_learner: PatternLearner,
        temporal_analyzer: TemporalAnalyzer,
        compliance_checker: ComplianceChecker,
    ) -> None:
        self.upload_data_service = upload_data_service
        self.analytics_service = analytics_service
        self.behavioral_analysis = behavior_analyzer
        self.security_refinement = security_refiner
        self.pattern_learning = pattern_learner
        self.temporal_analytics = temporal_analyzer
        self.compliance = compliance_checker

    # ------------------------------------------------------------------
    @override
    def enhance_metadata(self) -> Dict[str, Any]:
        """Run enhancement pipeline and return aggregated results."""
        uploaded = self.upload_data_service.get_uploaded_data()
        df = (
            pd.concat(uploaded.values(), ignore_index=True)
            if uploaded
            else pd.DataFrame()
        )

        return {
            "behavior": self.behavioral_analysis.analyze(df),
            "security": self.security_refinement.refine(df),
            "patterns": self.pattern_learning.learn(df),
            "temporal": self.temporal_analytics.analyze(df),
            "compliance": self.compliance.check(df),
            "analytics": self.analytics_service.get_dashboard_summary(),
        }


# ---------------------------------------------------------------------------
# Service registration helper
# ---------------------------------------------------------------------------


def register_metadata_services(container: ServiceContainer) -> None:
    """Register :class:`MetadataEnhancementEngine` with ``container``."""

    container.register_transient("behavior_analyzer", BehaviorAnalyzer)
    container.register_transient("security_refiner", SecurityRefiner)
    container.register_transient("pattern_learner", PatternLearner)
    container.register_transient("temporal_analyzer", TemporalAnalyzer)
    container.register_transient("compliance_checker", ComplianceChecker)

    container.register_singleton(
        "metadata_engine",
        MetadataEnhancementEngine,
        protocol=MetadataEnhancementProtocol,
    )
