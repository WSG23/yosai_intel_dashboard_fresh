"""Utility for resolving plugin load order based on dependencies."""

from __future__ import annotations

from typing import Iterable, Dict, List, Set

from .protocols import PluginProtocol


class CircularDependencyError(RuntimeError):
    """Raised when plugin dependencies contain a cycle."""


class PluginDependencyResolver:
    """Topologically sort plugins by their declared dependencies."""

    def __init__(self, plugins: Iterable[PluginProtocol]):
        self._plugins: Dict[str, PluginProtocol] = {
            p.metadata.name: p for p in plugins
        }
        # Preserve discovery order for deterministic sorting
        self._order: List[str] = [p.metadata.name for p in plugins]

    def resolve_dependencies(self) -> List[PluginProtocol]:
        """Return plugins sorted so that dependencies come before dependents."""
        graph: Dict[str, Set[str]] = {}
        for name, plugin in self._plugins.items():
            deps = getattr(plugin.metadata, "dependencies", None) or []
            for dep in deps:
                if dep not in self._plugins:
                    raise ValueError(
                        f"Plugin '{name}' depends on unknown plugin '{dep}'"
                    )
            graph[name] = set(deps)

        resolved: List[str] = []
        while graph:
            # Determine nodes without remaining dependencies respecting
            # discovery order for deterministic results
            ready = [n for n in self._order if n in graph and not graph[n]]
            if not ready:
                cycle = ", ".join(sorted(graph))
                raise CircularDependencyError(
                    f"Circular dependency detected among plugins: {cycle}"
                )

            for name in ready:
                resolved.append(name)
                del graph[name]
            for deps in graph.values():
                deps.difference_update(ready)

        return [self._plugins[name] for name in resolved]
