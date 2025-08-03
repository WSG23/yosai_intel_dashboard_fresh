"""Example demonstrating visualization helper usage."""

from __future__ import annotations

from yosai_intel_dashboard.src.infrastructure.monitoring.visualization import (
    distribution_plot,
    drift_chart,
    heatmap,
)


def main() -> None:
    values = [0.1, 0.2, 0.15, 0.3]
    drift_chart(values).savefig("drift.png")

    matrix = [[0.1, 0.2], [0.3, 0.4]]
    heatmap(matrix).savefig("heatmap.png")

    distribution_plot([1, 2, 2, 3, 4]).savefig("distribution.png")


if __name__ == "__main__":
    main()
