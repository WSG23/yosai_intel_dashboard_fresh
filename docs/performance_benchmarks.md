# Performance Benchmarks

This document summarises the performance characteristics of the
`GraphDB` component used by `intel_analysis_service`.

## Benchmark environment

- Synthetic fan-out graph with 10k nodes / 20k edges
- Intel Xeon (2 cores allocated in CI)
- Python's in-memory implementation with LRU caching

## Results

| Scenario                              | Metric           | Result |
|---------------------------------------|------------------|--------|
| Two-hop neighbourhood query           | latency          | <1 s   |
| Edge update                           | latency          | <100 ms|
| Concurrent queries (1000 threads)     | all completed    | yes    |

The benchmarks were executed via `pytest` in
`intel_analysis_service/tests/performance/`.

## Recent optimizations

- Hidden relationship detection now leverages `itertools.combinations`,
  shrinking runtime from **47.14 s** to **0.06 s** on a 150‑node/500‑edge
  graph.
- Dynamic SQL query builders use string joining rather than repeated
  concatenation, yielding small but measurable improvements in query
  assembly time.
- Data sensitivity scoring switches to generator expressions to avoid
  temporary list allocations.
- Automated performance analyzer now highlights inefficient string
  concatenations, nested loops, and large list comprehensions with file and
  line references.
- Boundary descriptions and data-quality alerts use f-strings instead of
  manual concatenation, reducing intermediate string objects.
- Legacy import checks leverage iterator chaining to avoid nested loops.
- Test data generators employ generator expressions for large ranges to
  minimize peak memory use.

## Database analytics service

Refactoring `AnalyticsService.get_analytics` to be fully asynchronous
removed repeated event loop creation. A follow‑up change awaits
`_gather_analytics` directly, eliminating the inner event loop. Measured
on a stubbed database connection executing two simple queries:

| Scenario                             | 5 calls total time |
|--------------------------------------|-------------------|
| Nested event loop (previous design)  | ~0.0145 s          |
| Direct await implementation          | ~0.0075 s          |

The direct `await` nearly halves total latency by avoiding redundant
event loop setup.

## Tuning notes

- Two-hop lookups utilise an LRU cache (`maxsize=100_000`).  Tune this
  based on available memory and query locality.
- Edge updates clear the cache to maintain correctness.  If update rates
  are high consider sharding the graph or switching to a distributed
  cache.
- Readers–writer locking favours read throughput.  For write-heavy
  workloads adjust the strategy accordingly.
