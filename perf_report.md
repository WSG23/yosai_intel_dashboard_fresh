# Callback Performance Report

This document outlines how callback execution times are captured and provides a space for recording results when optimising callbacks.

## Methodology

1. Each Dash callback is wrapped with the `measure_performance` decorator from `core.performance`.
2. The decorator records the execution time and stores metrics via the global performance monitor returned by `get_performance_monitor()`.
3. Metrics can be exported with `export_performance_report()` for further analysis.
4. Callbacks exceeding the configured threshold will be logged as slow operations.

## Running with Profiling Enabled

Set the environment variable `ENABLE_PROFILING` to `true` and start the app normally:

```bash
ENABLE_PROFILING=true python app.py
```

This loads the configuration values that enable performance monitoring within the application.

## Top 10 slow callbacks before optimisation

- TODO

## Top 10 slow callbacks after optimisation

- TODO
