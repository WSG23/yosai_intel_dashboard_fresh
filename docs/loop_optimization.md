# Loop Optimization Benchmarks

## UploadAnalyticsProcessor statistics calculation

- **Old:** nested loops over every row of each DataFrame to collect user and door IDs.
- **New:** hash-based set aggregation using `dropna().unique()` for each relevant column.

## Column name standardization

- **Old:** nested loops to build a reverse mapping from canonical headers and aliases.
- **New:** flattened hash map via set union and dictionary comprehension.

## Benchmarks

Run:

```bash
python scripts/benchmark_upload_processing.py
python scripts/benchmark_mapping_helpers.py
```

Example output:

```
Nested loops: 1.90s
Set aggregation: 0.056s
Old mapping: 0.023s
Hash map mapping: 0.021s
```
