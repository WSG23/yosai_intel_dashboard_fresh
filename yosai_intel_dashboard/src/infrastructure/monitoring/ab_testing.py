from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Callable, Dict, List, Optional

from scipy import stats

from monitoring import variant_hits


class ABTest:
    """Simple A/B testing utility.

    The class supports deterministic traffic assignment based on a user id,
    metric aggregation per variant, statistical significance testing and
    optional rollout strategies once a winner is determined.
    """

    def __init__(
        self,
        variants: Dict[str, float],
        metric_type: str = "binary",
        significance_level: float = 0.05,
    ) -> None:
        if metric_type not in {"binary", "continuous"}:
            raise ValueError("metric_type must be 'binary' or 'continuous'")
        total = float(sum(variants.values()))
        if total <= 0:
            raise ValueError("variants must have positive weights")
        self._thresholds: List[tuple[float, str]] = []
        cumulative = 0.0
        for variant, weight in variants.items():
            cumulative += weight / total
            self._thresholds.append((cumulative, variant))
        self.metric_type = metric_type
        self.significance_level = significance_level
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self._rollout_strategy: Optional[Callable[[str], None]] = None

    def assign(self, user_id: str | int) -> str:
        """Deterministically assign a user to a variant based on MD5 hash."""
        digest = hashlib.md5(str(user_id).encode()).hexdigest()
        value = int(digest, 16) / 2**128
        for threshold, variant in self._thresholds:
            if value < threshold:
                variant_hits.labels(variant=variant).inc()
                return variant
        variant = self._thresholds[-1][1]
        variant_hits.labels(variant=variant).inc()
        return variant

    def log_metric(self, variant: str, value: float) -> None:
        """Record a metric value for the given variant."""
        if variant not in {v for _, v in self._thresholds}:
            raise ValueError(f"Unknown variant: {variant}")
        self.metrics[variant].append(value)

    def set_rollout_strategy(self, strategy: Callable[[str], None]) -> None:
        """Register a strategy to rollout a winning variant."""
        self._rollout_strategy = strategy

    def evaluate(self) -> Optional[str]:
        """Evaluate the experiment and optionally rollout the winner."""
        if len(self.metrics) < 2:
            return None
        variants = list(self.metrics.keys())
        if self.metric_type == "continuous":
            if len(variants) != 2:
                raise ValueError("t-test supports exactly two variants")
            data1, data2 = self.metrics[variants[0]], self.metrics[variants[1]]
            stat, p_value = stats.ttest_ind(data1, data2, equal_var=False)
            if p_value < self.significance_level:
                winner = (
                    variants[0]
                    if sum(data1) / len(data1) > sum(data2) / len(data2)
                    else variants[1]
                )
            else:
                winner = None
        else:  # binary
            successes = [sum(self.metrics[v]) for v in variants]
            failures = [len(self.metrics[v]) - s for v, s in zip(variants, successes)]
            table = [successes, failures]
            chi2, p_value, _, _ = stats.chi2_contingency(table)
            if p_value < self.significance_level:
                rates = {
                    v: successes[i] / (successes[i] + failures[i])
                    for i, v in enumerate(variants)
                }
                winner = max(rates, key=rates.get)
            else:
                winner = None
        if winner and self._rollout_strategy:
            self._rollout_strategy(winner)
        return winner


__all__ = ["ABTest"]
