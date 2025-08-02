from __future__ import annotations

"""Simple drift detection utilities."""

from typing import Dict

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from scipy.stats import wasserstein_distance as _wasserstein_distance


def population_stability_index(
    expected: pd.Series, actual: pd.Series, *, bins: int = 10
) -> float:
    """Calculate the Population Stability Index (PSI)."""
    expected = expected.dropna()
    actual = actual.dropna()
    exp_counts, bin_edges = np.histogram(expected, bins=bins)
    act_counts, _ = np.histogram(actual, bins=bin_edges)

    exp_perc = exp_counts / exp_counts.sum() if exp_counts.sum() > 0 else exp_counts
    act_perc = act_counts / act_counts.sum() if act_counts.sum() > 0 else act_counts

    # avoid zeros which break the log calculation
    exp_perc = np.where(exp_perc == 0, 1e-6, exp_perc)
    act_perc = np.where(act_perc == 0, 1e-6, act_perc)
    psi = np.sum((act_perc - exp_perc) * np.log(act_perc / exp_perc))
    return float(psi)


def compute_psi(
    base: pd.DataFrame, current: pd.DataFrame, *, bins: int = 10
) -> Dict[str, float]:
    """Return PSI for all common columns between ``base`` and ``current``."""
    metrics: Dict[str, float] = {}
    for col in base.columns.intersection(current.columns):
        metrics[col] = population_stability_index(base[col], current[col], bins=bins)
    return metrics


def kolmogorov_smirnov(base: pd.Series, current: pd.Series) -> float:
    """Return the Kolmogorov-Smirnov statistic for two samples."""
    base = base.dropna()
    current = current.dropna()
    statistic, _ = ks_2samp(base, current)
    return float(statistic)


def wasserstein_distance(base: pd.Series, current: pd.Series) -> float:
    """Return the first Wasserstein distance between two samples."""
    base = base.dropna()
    current = current.dropna()
    return float(_wasserstein_distance(base, current))


def detect_drift(
    base: pd.DataFrame, current: pd.DataFrame, *, bins: int = 10
) -> Dict[str, Dict[str, float]]:
    """Return PSI, KS, and Wasserstein metrics for common columns."""
    metrics: Dict[str, Dict[str, float]] = {}
    for col in base.columns.intersection(current.columns):
        metrics[col] = {
            "psi": population_stability_index(base[col], current[col], bins=bins),
            "ks": kolmogorov_smirnov(base[col], current[col]),
            "wasserstein": wasserstein_distance(base[col], current[col]),
        }
    return metrics


__all__ = [
    "population_stability_index",
    "compute_psi",
    "kolmogorov_smirnov",
    "wasserstein_distance",
    "detect_drift",
]
