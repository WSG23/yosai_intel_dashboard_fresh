# Visualization Style Guide

This guide standardizes how visual elements appear across the dashboard. Each section shows the preferred styling and a minimal code sample using the built-in helpers.

## Drift Chart

Use line charts to display model drift or other time‑series metrics.

```python
from yosai_intel_dashboard.src.infrastructure.monitoring.visualization import drift_chart

fig = drift_chart([0.1, 0.2, 0.15, 0.3])
fig.savefig("drift.png")
```

## Heatmap

Heatmaps visualize matrix data such as correlations.

```python
from yosai_intel_dashboard.src.infrastructure.monitoring.visualization import heatmap

matrix = [[0.1, 0.2], [0.3, 0.4]]
fig = heatmap(matrix)
fig.savefig("heatmap.png")
```

## Distribution Plot

Histograms show how values are distributed.

```python
from yosai_intel_dashboard.src.infrastructure.monitoring.visualization import distribution_plot

fig = distribution_plot([1, 2, 2, 3, 4])
fig.savefig("distribution.png")
```
