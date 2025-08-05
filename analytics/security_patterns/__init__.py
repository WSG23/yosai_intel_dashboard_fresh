from __future__ import annotations

import contextlib
import io
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.callbacks.events import (
    CallbackEvent as SecurityEvent,
)
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
    TrulyUnifiedCallbacks,
)

from .odd_time_detection import detect_odd_time
from .pattern_detection import Threat, detect_critical_door_risks

# Fallback callback manager used if ``security.events`` cannot be imported.
fallback_callbacks: TrulyUnifiedCallbacks | None = None


# ---------------------------------------------------------------------------
# Public helpers


def prepare_security_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare raw access log dataframe for pattern analysis."""
    df = df.copy()
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["hour"] = df["timestamp"].dt.hour
    return df


class SecurityPatternsAnalyzer:
    """Very small analyzer used in tests."""

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        return prepare_security_data(df)

    def _analyze_failed_access(self, df: pd.DataFrame) -> Dict[str, Any]:
        failures = df[df.get("access_result") == "Denied"]
        total = len(failures)
        total_events = len(df) or 1
        failure_rate = total / total_events
        high_risk_users = failures["person_id"].value_counts().head(3).to_dict()
        peak_failure_times = failures["hour"].value_counts().head(3).to_dict()
        top_failure_doors = failures["door_id"].value_counts().head(3).to_dict()
        patterns: List[Any] = []
        risk_level = "low"
        if failure_rate > 0.5:
            risk_level = "high"
        elif failure_rate > 0.2:
            risk_level = "medium"
        return {
            "total": total,
            "failure_rate": failure_rate,
            "high_risk_users": high_risk_users,
            "peak_failure_times": peak_failure_times,
            "top_failure_doors": top_failure_doors,
            "patterns": patterns,
            "risk_level": risk_level,
        }

    def analyze_security_patterns(self, df: pd.DataFrame) -> List[Threat]:
        prepared = self._prepare_data(df)
        threats = list(detect_critical_door_risks(prepared))
        threats.extend(_detect_rapid_failures(prepared))
        try:  # pragma: no cover - import may fail in test environment
            from yosai_intel_dashboard.src.infrastructure.security import (
                events as se,  # type: ignore
            )

            manager = se.security_unified_callbacks
        except Exception:  # pragma: no cover
            manager = fallback_callbacks
        if manager is None:
            manager = TrulyUnifiedCallbacks()
        if threats:
            manager.trigger_event(SecurityEvent.THREAT_DETECTED, {"threats": threats})
        manager.trigger_event(
            SecurityEvent.ANALYSIS_COMPLETE, {"records": len(prepared)}
        )
        return threats


# ---------------------------------------------------------------------------
# Test data generators


def generate_failed_access(count: int = 3) -> pd.DataFrame:
    """Generate a dataframe representing failed access attempts."""
    ts = pd.Timestamp("2024-01-01 00:00:00")
    data = [
        {
            "event_id": i,
            "timestamp": ts + pd.Timedelta(minutes=i),
            "person_id": f"u{i%2}",
            "door_id": "d1",
            "access_result": "Denied",
        }
        for i in range(count)
    ]
    return pd.DataFrame(data)


def generate_threat_attempt() -> pd.DataFrame:
    """Generate data that should trigger a critical threat."""
    ts = pd.Timestamp("2024-01-01 00:00:00")
    data = []
    for i in range(4):
        data.append(
            {
                "event_id": i,
                "timestamp": ts + pd.Timedelta(seconds=i * 5),
                "person_id": "baduser",
                "door_id": "d1",
                "access_result": "Denied",
                "door_type": "critical",
                "required_clearance": 4,
                "clearance_level": 1,
            }
        )
    return pd.DataFrame(data)


def _detect_rapid_failures(df: pd.DataFrame) -> List[Threat]:
    failures = df[df.get("access_result") == "Denied"].copy()
    if failures.empty:
        return []

    summary = failures.groupby("person_id")["timestamp"].agg(["count", "min", "max"])
    summary["window"] = (summary["max"] - summary["min"]).dt.total_seconds()
    mask = (summary["count"] >= 3) & (summary["window"] <= 60)
    return [
        Threat("rapid_denied_access", {"person_id": person})
        for person in summary[mask].index
    ]


# ---------------------------------------------------------------------------
# Isolated testing context


@dataclass
class SecurityTestEnv:
    callback_manager: TrulyUnifiedCallbacks
    events: Dict[SecurityEvent, List[Any]]
    logger: logging.Logger
    log_stream: io.StringIO


@contextlib.contextmanager
def setup_isolated_security_testing() -> Any:
    """Provide an isolated security testing environment."""
    global fallback_callbacks
    try:  # pragma: no cover - may fail if heavy deps missing
        new_manager = TrulyUnifiedCallbacks()
    except Exception:  # pragma: no cover
        new_manager = TrulyUnifiedCallbacks()
    fallback_callbacks = new_manager
    try:  # pragma: no cover - import may fail if optional deps missing
        from yosai_intel_dashboard.src.infrastructure.security import (
            events as se,  # type: ignore
        )

        original_manager = se.security_unified_callbacks
        se.security_unified_callbacks = new_manager
    except Exception:  # pragma: no cover
        se = None
        original_manager = None

    captured: Dict[SecurityEvent, List[Any]] = {e: [] for e in SecurityEvent}
    for event in SecurityEvent:
        new_manager.register_event(event, lambda d, ev=event: captured[ev].append(d))

    logger = logging.getLogger("analytics.security_patterns.tests")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    orig_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    env = SecurityTestEnv(
        callback_manager=new_manager, events=captured, logger=logger, log_stream=stream
    )

    try:
        yield env
    finally:
        new_manager.clear_all_callbacks()
        for lst in captured.values():
            lst.clear()
        logger.removeHandler(handler)
        logger.setLevel(orig_level)
        handler.close()
        stream.close()
        fallback_callbacks = None
        if original_manager is not None and se is not None:
            se.security_unified_callbacks = original_manager


__all__ = [
    "SecurityEvent",
    "SecurityPatternsAnalyzer",
    "setup_isolated_security_testing",
    "prepare_security_data",
    "generate_failed_access",
    "generate_threat_attempt",
    "SecurityTestEnv",
    "detect_critical_door_risks",
    "detect_odd_time",
]
