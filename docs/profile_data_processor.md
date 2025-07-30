# Profiling the Data Processor

Use `tools/profile_data_processor.py` to profile `DataProcessor.process`.
The script can run either `cProfile` or `pyinstrument` and prints the most expensive calls.
When using cProfile a dump is written to `profile.prof` (or the `--output` path).
With pyinstrument an HTML report is generated instead.

```bash
# cProfile
python tools/profile_data_processor.py big_dataset.csv -o dp.prof

# pyinstrument
python tools/profile_data_processor.py big_dataset.csv --tool pyinstrument -o profile.html
```

You can load the `.prof` file with standard tools like `snakeviz` or
`pstats` for further analysis.
