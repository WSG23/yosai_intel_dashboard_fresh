"""Simple plotting utilities for monitoring visualizations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

import matplotlib

from services.export import ExportService

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

_EXPORTER = ExportService()


@dataclass
class Visualization:
    """Visualization metadata with collaboration helpers."""

    figure: plt.Figure
    shareable_link: str
    embed_code: str
    view_id: str
    annotations: List[str] = field(default_factory=list)
    version: int = 1

    def annotate(self, note: str) -> None:
        """Attach an annotation and bump the version."""

        view = _EXPORTER.add_annotation(self.view_id, note)
        self.annotations = view.annotations
        self.version = view.version


def _build_visualization(fig: plt.Figure, fmt: str) -> Visualization:
    view_id, link, embed = _EXPORTER.create_shareable(fig, fmt)
    view = _EXPORTER.get_view(view_id)
    return Visualization(fig, link, embed, view_id, view.annotations, view.version)


def drift_chart(values: Sequence[float], fmt: str = "html") -> Visualization:
    """Generate a line chart representing drift over time."""

    fig, ax = plt.subplots()
    ax.plot(list(values))
    ax.set_title("Drift")
    return _build_visualization(fig, fmt)


def heatmap(matrix: Sequence[Sequence[float]], fmt: str = "html") -> Visualization:
    """Generate a heatmap from a 2D matrix."""

    fig, ax = plt.subplots()
    ax.imshow(matrix, aspect="auto")
    ax.set_title("Heatmap")
    return _build_visualization(fig, fmt)


def distribution_plot(values: Iterable[float], fmt: str = "html") -> Visualization:
    """Generate a histogram to visualize a distribution."""

    fig, ax = plt.subplots()
    ax.hist(list(values), bins=10)
    ax.set_title("Distribution")
    return _build_visualization(fig, fmt)


__all__ = [
    "Visualization",
    "drift_chart",
    "heatmap",
    "distribution_plot",
]
