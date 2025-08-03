# Visualization API

Utilities for generating common charts live in `yosai_intel_dashboard.src.infrastructure.monitoring.visualization`.

## `drift_chart(values: Sequence[float])`

Returns a Matplotlib figure showing value drift over time.

```python
from yosai_intel_dashboard.src.infrastructure.monitoring.visualization import drift_chart

fig = drift_chart([0.1, 0.2, 0.15])
fig.savefig("drift.png")
```

## `heatmap(matrix: Sequence[Sequence[float]])`

Renders a heatmap of the supplied matrix.

```python
from yosai_intel_dashboard.src.infrastructure.monitoring.visualization import heatmap

matrix = [[0.1, 0.2], [0.3, 0.4]]
fig = heatmap(matrix)
fig.savefig("heatmap.png")
```

## `distribution_plot(values: Iterable[float])`

Produces a histogram of the input values.

```python
from yosai_intel_dashboard.src.infrastructure.monitoring.visualization import distribution_plot

fig = distribution_plot([1, 2, 2, 3, 4])
fig.savefig("distribution.png")
```
