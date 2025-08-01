# PerformanceFileProcessor

The `PerformanceFileProcessor` assists with reading very large CSV files
while keeping memory usage under control. Data is streamed in chunks and
the current memory footprint can be observed after each chunk.

```python
from yosai_intel_dashboard.src.core.performance_file_processor import PerformanceFileProcessor

processor = PerformanceFileProcessor(chunk_size=50_000)

# Optional callback receives rows processed and memory usage in MB
progress = lambda rows, mem: print(f"{rows} rows - {mem:.1f} MB")

df = processor.process_large_csv("big_data.csv", progress_callback=progress)
```

Providing a callback is optional; the method simply returns the combined
`DataFrame` after all chunks have been concatenated.

The `process_large_csv` method accepts an optional `max_memory_mb` argument to
flush intermediate chunks once the process memory exceeds the threshold.  When
``stream=True`` is passed, the method yields `DataFrame` objects instead of
returning a single combined result:

```python
for chunk in processor.process_large_csv(
        "big_data.csv",
        progress_callback=progress,
        max_memory_mb=500,
        stream=True,
):
    handle_chunk(chunk)
```

This streaming mode lets you work with very large files without loading the
entire dataset into memory at once.
