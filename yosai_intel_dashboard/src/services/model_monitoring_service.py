from __future__ import annotations

"""Model monitoring utilities with alerting support."""

import logging
import os
from typing import Optional

import numpy as np
import pandas as pd

from services.monitoring.drift import compute_psi
from core.monitoring.user_experience_metrics import AlertConfig, AlertDispatcher

try:  # pragma: no cover - optional dependency
    from scipy.stats import ks_2samp, wasserstein_distance
except Exception:  # pragma: no cover - allow running without SciPy

    def ks_2samp(a: np.ndarray, b: np.ndarray):
        return 0.0, 1.0

    def wasserstein_distance(a: np.ndarray, b: np.ndarray) -> float:
        return 0.0


log = logging.getLogger(__name__)


class ModelMonitoringService:
    """Compare inference data against baseline and dispatch alerts."""

    def __init__(
        self, dispatcher: Optional[AlertDispatcher] = None
    ) -> None:
        self.ks_threshold = float(os.getenv("KS_THRESHOLD", "0.1"))
        self.psi_threshold = float(os.getenv("PSI_THRESHOLD", "0.1"))
        self.wasserstein_threshold = float(
            os.getenv("WASSERSTEIN_THRESHOLD", "0.1")
        )

        alert_cfg = AlertConfig(
            slack_webhook=os.getenv("ALERT_SLACK_WEBHOOK"),
            email=os.getenv("ALERT_EMAIL"),
            webhook_url=os.getenv("ALERT_WEBHOOK_URL"),
        )
        self.dispatcher = dispatcher or AlertDispatcher(alert_cfg)

    # ------------------------------------------------------------------
    def check_drift(self, baseline: pd.DataFrame, current: pd.DataFrame) -> None:
        """Evaluate drift metrics and send alerts when thresholds exceeded."""

        problems: list[str] = []
        psi_metrics = compute_psi(baseline, current)

        for col in baseline.columns.intersection(current.columns):
            base_col = baseline[col].dropna()
            cur_col = current[col].dropna()
            if base_col.empty or cur_col.empty:
                continue

            ks_stat, _ = ks_2samp(base_col.values, cur_col.values)
            psi = psi_metrics.get(col, 0.0)
            wasser = wasserstein_distance(base_col.values, cur_col.values)

            if ks_stat > self.ks_threshold:
                problems.append(
                    f"{col} KS {ks_stat:.3f} > {self.ks_threshold:.3f}"
                )
            if psi > self.psi_threshold:
                problems.append(
                    f"{col} PSI {psi:.3f} > {self.psi_threshold:.3f}"
                )
            if wasser > self.wasserstein_threshold:
                problems.append(
                    f"{col} Wasserstein {wasser:.3f} > {self.wasserstein_threshold:.3f}"
                )

        if problems:
            message = "Model monitoring alert: " + "; ".join(problems)
            try:
                self.dispatcher.send_alert(message)
            except Exception as exc:  # pragma: no cover - alert failures
                log.warning("Alert dispatch failed: %s", exc)


__all__ = ["ModelMonitoringService"]

