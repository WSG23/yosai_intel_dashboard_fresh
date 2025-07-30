# Profiling the Data Processor

Use `tools/profile_data_processor.py` to profile `DataProcessor.process` with `cProfile`.
The script runs the pipeline on a given file and prints the most expensive calls.
A profile dump is also written to `profile.prof` unless you specify a different
output path with `--output`.

```bash
python tools/profile_data_processor.py big_dataset.csv -o dp.prof
```

You can load the `.prof` file with standard tools like `snakeviz` or
`pstats` for further analysis.
