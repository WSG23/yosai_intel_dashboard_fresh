from __future__ import annotations

# Dev shim for analytics.core.utils expected by the real API.
# Provides a simple cardinality estimator compatible with the real import.
# TODO: replace with the production implementation when available.

def hll_count(iterable) -> int:
    try:
        return len({x for x in iterable})
    except TypeError:
        # Non-hashable items: fallback to string repr
        return len({repr(x) for x in iterable})
