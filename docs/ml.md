# Machine learning metrics

The machine learning services expose several Prometheus metrics to assist with
monitoring.

### Drift detection

`drift_detection_results_total{detected="<bool>"}`

: Counts each invocation of the drift detector and whether drift was detected.
  A label of `detected="true"` represents drift, while `false` indicates a
  clean check.

