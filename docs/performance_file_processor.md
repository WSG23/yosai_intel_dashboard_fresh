# PerformanceFileProcessor

The `PerformanceFileProcessor` assists with reading very large CSV files
while keeping memory usage under control. Data is streamed in chunks and
the current memory footprint can be observed after each chunk.

```python
from core import PerformanceFileProcessor

processor = PerformanceFileProcessor(chunk_size=50_000)

# Optional callback receives rows processed and memory usage in MB
progress = lambda rows, mem: print(f"{rows} rows - {mem:.1f} MB")

df = processor.process_large_csv("big_data.csv", progress_callback=progress)
```

Providing a callback is optional; the method simply returns the combined
`DataFrame` after all chunks have been concatenated.
