from __future__ import annotations

"""Simple drift detection utilities."""

from typing import Dict

import numpy as np
import pandas as pd


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


__all__ = ["population_stability_index", "compute_psi"]
