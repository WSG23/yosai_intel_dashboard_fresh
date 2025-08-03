"""Error budget tracking and Prometheus metrics."""

from __future__ import annotations

import os
from typing import Callable, Dict

from prometheus_client import REGISTRY, Counter, Gauge, CollectorRegistry

# Default per-service budget if none configured
_DEFAULT_BUDGET = int(os.getenv("ERROR_BUDGET_DEFAULT", 1000))

# Store configured budgets parsed from the ERROR_BUDGETS env var. The value
# should be a comma separated list like "api=1000,worker=500".
_BUDGETS: Dict[str, int] = {}

for part in os.getenv("ERROR_BUDGETS", "").split(","):
    if not part:
        continue
    name, _, value = part.partition("=")
    try:
        _BUDGETS[name.strip()] = int(value)
    except ValueError:
        continue

if "service_errors_total" not in REGISTRY._names_to_collectors:
    service_errors = Counter(
        "service_errors_total", "Total number of errors per service", ["service"],
    )
else:  # pragma: no cover - tests may register their own collector
    service_errors = Counter(
        "service_errors_total",
        "Total number of errors per service",
        ["service"],
        registry=CollectorRegistry(),
    )

if "service_error_budget_remaining" not in REGISTRY._names_to_collectors:
    error_budget_remaining = Gauge(
        "service_error_budget_remaining",
        "Remaining error budget per service",
        ["service"],
    )
else:  # pragma: no cover - tests may register their own collector
    error_budget_remaining = Gauge(
        "service_error_budget_remaining",
        "Remaining error budget per service",
        ["service"],
        registry=CollectorRegistry(),
    )


def _budget_for(service: str) -> int:
    """Return configured budget for *service* or the default."""
    return _BUDGETS.get(service, _DEFAULT_BUDGET)


def set_budget(service: str, budget: int) -> None:
    """Configure the error budget for *service*."""
    _BUDGETS[service] = budget
    error_budget_remaining.labels(service).set(budget - service_errors.labels(service)._value.get())


def record_error(service: str) -> None:
    """Increment error counters for *service* and update remaining budget."""
    service_errors.labels(service).inc()
    remaining = _budget_for(service) - service_errors.labels(service)._value.get()
    error_budget_remaining.labels(service).set(max(0, remaining))


def get_remaining_budget(service: str) -> float:
    """Return the current remaining error budget for *service*."""
    return error_budget_remaining.labels(service)._value.get()


def is_budget_exhausted(service: str) -> bool:
    """Return ``True`` if *service* has exhausted its error budget."""
    return get_remaining_budget(service) <= 0


def alert_if_exhausted(service: str, alert: Callable[[str], None]) -> None:
    """Invoke *alert* callback when the error budget for *service* is exhausted."""
    if is_budget_exhausted(service):
        alert(service)


__all__ = [
    "service_errors",
    "error_budget_remaining",
    "record_error",
    "get_remaining_budget",
    "is_budget_exhausted",
    "alert_if_exhausted",
    "set_budget",
]
