"""Simple plotting utilities for monitoring visualizations."""
from __future__ import annotations

from typing import Iterable, Sequence

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def drift_chart(values: Sequence[float]):
    """Generate a line chart representing drift over time."""
    fig, ax = plt.subplots()
    ax.plot(list(values))
    ax.set_title('Drift')
    return fig


def heatmap(matrix: Sequence[Sequence[float]]):
    """Generate a heatmap from a 2D matrix."""
    fig, ax = plt.subplots()
    ax.imshow(matrix, aspect='auto')
    ax.set_title('Heatmap')
    return fig


def distribution_plot(values: Iterable[float]):
    """Generate a histogram to visualize a distribution."""
    fig, ax = plt.subplots()
    ax.hist(list(values), bins=10)
    ax.set_title('Distribution')
    return fig


__all__ = ['drift_chart', 'heatmap', 'distribution_plot']
