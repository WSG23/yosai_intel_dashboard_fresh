"""Compatibility helpers for SciPy internals."""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def get_wrap_callback() -> Callable[..., Any]:
    """Return SciPy's private ``_wrap_callback`` implementation.

    Handles different module locations across SciPy versions.
    """
    try:
        from scipy.optimize._optimize import _wrap_callback
        return _wrap_callback
    except Exception:
        try:
            from scipy.optimize.optimize import _wrap_callback  # type: ignore
            return _wrap_callback
        except Exception as exc:  # pragma: no cover - fallback
            logger.warning("_wrap_callback unavailable: %s", exc)

            def _wrap_callback(f: Callable[..., Any], c: Any) -> Callable[..., Any]:
                def wrapper(xk: Any, *a: Any, **kw: Any) -> Any:
                    return f(xk, *a, **kw)

                return wrapper

            return _wrap_callback


import numpy as np


class FallbackStats:
    @staticmethod
    def zscore(a, axis=0, ddof=0, nan_policy='propagate'):
        a = np.asarray(a)
        if axis is None:
            a = a.ravel()
            axis = 0
        mean = np.mean(a, axis=axis, keepdims=True)
        std = np.std(a, axis=axis, ddof=ddof, keepdims=True)
        with np.errstate(divide='ignore', invalid='ignore'):
            z = (a - mean) / std
            z = np.where(std == 0, 0, z)
        return z


def get_stats_module():
    try:
        from scipy import stats
        return stats
    except Exception as exc:
        logger.warning("scipy.stats unavailable: %s", exc)
        return FallbackStats()


__all__ = ["get_wrap_callback", "get_stats_module"]

