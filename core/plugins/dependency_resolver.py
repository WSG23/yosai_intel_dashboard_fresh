from __future__ import annotations

from typing import List, Dict, Set

from .protocols import PluginProtocol


class PluginDependencyResolver:
    """Simple dependency resolver using plugin metadata."""

    def resolve(self, plugins: List[PluginProtocol]) -> List[PluginProtocol]:
        name_map: Dict[str, PluginProtocol] = {p.metadata.name: p for p in plugins if hasattr(p, "metadata")}
        graph: Dict[str, Set[str]] = {
            p.metadata.name: set(getattr(p.metadata, "dependencies", []) or [])
            for p in plugins
            if hasattr(p, "metadata")
        }

        resolved: List[PluginProtocol] = []
        visited: Set[str] = set()

        def visit(name: str, stack: Set[str]) -> None:
            if name in visited:
                return
            if name in stack:
                raise ValueError(f"Circular dependency detected: {name}")
            stack.add(name)
            for dep in graph.get(name, set()):
                if dep in name_map:
                    visit(dep, stack)
            stack.remove(name)
            visited.add(name)
            resolved.append(name_map[name])

        for plugin in plugins:
            if hasattr(plugin, "metadata"):
                visit(plugin.metadata.name, set())
            else:
                resolved.append(plugin)
        return resolved
