import hashlib
from typing import Any, Dict, Optional, Set


class FlagEvaluator:
    """Evaluate feature flags with dependencies and rollout rules."""

    def __init__(self, flags: Dict[str, Any]) -> None:
        self._flags = flags

    def _hash(self, user_id: str, modulo: int) -> int:
        """Return deterministic bucket for *user_id* within ``modulo``."""
        digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % modulo

    def evaluate(
        self,
        name: str,
        user_id: Optional[str] = None,
        _stack: Optional[Set[str]] = None,
    ) -> Any:
        """Return variant string or boolean for *name* flag.

        Parameters
        ----------
        name:
            Flag name to evaluate.
        user_id:
            Optional user identifier used for targeted or percentage rollouts.
        _stack:
            Internal set for tracking dependency recursion.
        """
        flag = self._flags.get(name)
        if flag is None:
            return None

        if _stack is None:
            _stack = set()
        if name in _stack:
            return None
        _stack.add(name)

        # Dependencies -----------------------------------------------------
        for dep in flag.get("dependencies", []):
            if not self.evaluate(dep, user_id, _stack):
                return False

        # Targeted rules ---------------------------------------------------
        if user_id:
            for rule in flag.get("rules", []):
                targets = rule.get("user_ids") or []
                if user_id in targets:
                    return rule.get("variant", True)

        # Variants / percentage rollout ------------------------------------
        if user_id:
            variants = flag.get("variants")
            if isinstance(variants, dict) and variants:
                total = 0
                weights = []
                for var, weight in variants.items():
                    try:
                        w = int(weight)
                    except Exception:
                        continue
                    total += w
                    weights.append((var, w))
                if total > 0:
                    bucket = self._hash(user_id, total)
                    acc = 0
                    for var, weight in weights:
                        acc += weight
                        if bucket < acc:
                            return var
            percentage = flag.get("percentage") or flag.get("rollout")
            if percentage is not None:
                try:
                    pct = int(percentage)
                except Exception:
                    pct = 0
                bucket = self._hash(user_id, 100)
                return bucket < pct

        # Default ----------------------------------------------------------
        return flag.get("default", False)
