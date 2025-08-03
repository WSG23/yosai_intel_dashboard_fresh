from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FlagEvaluator:
    """Evaluate feature flags with dependency resolution.

    Flags are loaded from Redis as a JSON mapping. Each flag record may
    contain:

    ``value``: The value of the flag when all dependencies are enabled.
    ``fallback``: Value returned if a dependency resolves to off.
    ``dependencies``: List of prerequisite flag names.
    """

    def __init__(self, redis_client: Any, key: str = "feature_flags") -> None:
        self.redis = redis_client
        self.key = key
        self.flags: Dict[str, Dict[str, Any]] = {}
        self.order: List[str] = []
        self._load_flags()

    # ------------------------------------------------------------------
    def _load_flags(self) -> None:
        """Load flag definitions from Redis and build dependency graph."""

        raw = self.redis.get(self.key)
        if not raw:
            self.flags = {}
            self.order = []
            return
        try:
            data = json.loads(raw)
        except Exception:  # pragma: no cover - defensive
            logger.warning("Invalid flag data for %s", self.key)
            self.flags = {}
            self.order = []
            return

        self.flags = {name: self._normalize(rec) for name, rec in data.items()}
        self.order = self._topological_sort()

    # ------------------------------------------------------------------
    def _normalize(self, record: Any) -> Dict[str, Any]:
        if isinstance(record, bool):
            return {"value": record, "fallback": False, "dependencies": []}
        if isinstance(record, dict):
            deps = record.get("dependencies") or []
            if not isinstance(deps, list):
                deps = []
            return {
                "value": bool(record.get("value", record.get("enabled", False))),
                "fallback": bool(record.get("fallback", False)),
                "dependencies": [str(d) for d in deps],
            }
        return {"value": False, "fallback": False, "dependencies": []}

    # ------------------------------------------------------------------
    def _topological_sort(self) -> List[str]:
        graph = {name: rec["dependencies"] for name, rec in self.flags.items()}
        order: List[str] = []
        temp: set[str] = set()
        perm: set[str] = set()

        def visit(node: str, stack: List[str]) -> None:
            if node in perm:
                return
            if node in temp:
                cycle = " -> ".join(stack + [node])
                raise ValueError(f"Dependency cycle detected: {cycle}")
            temp.add(node)
            for dep in graph.get(node, []):
                if dep in graph:
                    visit(dep, stack + [node])
            temp.remove(node)
            perm.add(node)
            order.append(node)

        for node in graph:
            visit(node, [])
        return order

    # ------------------------------------------------------------------
    def evaluate(self, name: str) -> bool:
        """Evaluate *name* flag considering its dependencies."""

        cache: Dict[str, bool] = {}

        def eval_flag(flag: str) -> bool:
            if flag in cache:
                return cache[flag]
            rec = self.flags.get(flag)
            if rec is None:
                cache[flag] = False
                return False
            for dep in rec["dependencies"]:
                if not eval_flag(dep):
                    cache[flag] = rec.get("fallback", False)
                    return cache[flag]
            cache[flag] = rec["value"]
            return cache[flag]

        return eval_flag(name)
