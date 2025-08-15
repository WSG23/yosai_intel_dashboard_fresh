"""Feature pipelines for context-aware models.

This module exposes utilities to merge several event streams into a single
feature DataFrame used by downstream models.  Each event stream is expected to
contain a ``timestamp`` column which will be used for alignment.
"""

from __future__ import annotations

from functools import reduce
from pathlib import Path
from typing import Iterable

try:  # pragma: no cover - optional dependency
    import opentelemetry.trace as trace

    tracer = trace.get_tracer(__name__)
except Exception:  # pragma: no cover - fallback when OpenTelemetry missing

    class _DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_attribute(self, *args, **kwargs):
            return None

    class _Tracer:
        def start_as_current_span(self, *_a, **_k):
            return _DummySpan()

    tracer = _Tracer()
import pandas as pd

try:  # pragma: no cover - optional dependency
    import pyarrow as pa

    _HAVE_ARROW = hasattr(pa, "Table")
except Exception:  # pragma: no cover - pyarrow not installed or stubbed
    pa = None
    _HAVE_ARROW = False


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure a DataFrame has a ``timestamp`` column and is sorted."""
    if "timestamp" not in df:
        raise KeyError("DataFrame must contain 'timestamp' column")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp")


def build_context_features(
    weather_events: pd.DataFrame,
    events: pd.DataFrame,
    transport_events: pd.DataFrame,
    social_signals: pd.DataFrame,
    infrastructure_events: pd.DataFrame,
    *,
    cache_path: str | Path | None = None,
    use_pyarrow: bool = True,
    streaming: bool = True,
    chunk_size: int | None = 100_000,
) -> pd.DataFrame:
    """Combine heterogeneous event streams into a single feature set.

    Parameters
    ----------
    weather_events, events, transport_events, social_signals, infrastructure_events:
        DataFrames with a ``timestamp`` column.  The remaining columns represent
        features to be used for modeling.
    cache_path:
        Optional path where the resulting DataFrame will be cached as parquet.
    use_pyarrow:
        When ``True`` and pyarrow is installed the join is executed using
        ``pyarrow.Table.join`` which is generally faster and more memory
        efficient.
    streaming:
        If ``True`` (default) the pandas fallback performs a streaming/ chunked
        join to reduce peak memory usage.  When ``False`` the previous
        ``pandas.merge`` based implementation is used, which is useful for
        benchmarking.
    chunk_size:
        Number of rows to process per chunk when ``streaming`` is enabled.  If
        ``None`` the entire dataset is processed in one pass.

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by timestamp containing the union of all features.  All
        missing values are filled with ``0``.
    """

    with tracer.start_as_current_span("build_context_features"):
        dataframes: Iterable[pd.DataFrame] = (
            weather_events,
            events,
            transport_events,
            social_signals,
            infrastructure_events,
        )

        normalized: list[pd.DataFrame] = [_normalize(df) for df in dataframes]

        cache_file = Path(cache_path) if cache_path else None
        if cache_file and cache_file.exists():
            return pd.read_parquet(cache_file)

        if use_pyarrow and _HAVE_ARROW:
            tables = [
                pa.Table.from_pandas(df, preserve_index=False) for df in normalized
            ]
            merged = reduce(
                lambda left, right: left.join(
                    right, keys="timestamp", join_type="full outer"
                ),
                tables,
            )
            features = merged.to_pandas()
        else:
            if streaming:
                frames = [df.set_index("timestamp") for df in normalized]
                index = frames[0].index
                for frame in frames[1:]:
                    index = index.union(frame.index)
                index = index.sort_values()
                if chunk_size and len(index) > chunk_size:
                    chunks: list[pd.DataFrame] = []
                    for start in range(0, len(index), chunk_size):
                        idx = index[start : start + chunk_size]
                        chunk = pd.concat([f.reindex(idx) for f in frames], axis=1)
                        chunks.append(chunk)
                    merged = pd.concat(chunks)
                else:
                    merged = pd.concat(frames, axis=1).reindex(index)
                merged.index.name = "timestamp"
                features = merged.reset_index()
            else:
                features = reduce(
                    lambda left, right: pd.merge(
                        left, right, on="timestamp", how="outer"
                    ),
                    normalized,
                )

        features = features.sort_values("timestamp").fillna(0)

        if "events" in features:
            features["event_density"] = (
                features["events"].rolling(window=3, min_periods=1).sum()
            )
        if "social" in features:
            features["social_sentiment"] = (
                features["social"].rolling(window=3, min_periods=1).mean()
            )

        if cache_file:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            features.to_parquet(cache_file)

        return features
