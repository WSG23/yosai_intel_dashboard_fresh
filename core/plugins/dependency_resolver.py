
from __future__ import annotations

from typing import List, Dict, Set, DefaultDict

from .protocols import PluginProtocol


class PluginDependencyResolver:
    """Simple dependency resolver using plugin metadata."""

    def resolve(self, plugins: List[PluginProtocol]) -> List[PluginProtocol]:
        plugins_with_meta = [p for p in plugins if hasattr(p, "metadata")]
        plugins_without_meta = [p for p in plugins if not hasattr(p, "metadata")]

        name_map: Dict[str, PluginProtocol] = {
            p.metadata.name: p for p in plugins_with_meta
        }

        adjacency: DefaultDict[str, Set[str]] = DefaultDict(set)
        in_degree: Dict[str, int] = {}
        missing: Set[str] = set()

        for plugin in plugins_with_meta:
            name = plugin.metadata.name
            deps = getattr(plugin.metadata, "dependencies", []) or []
            in_degree.setdefault(name, 0)
            for dep in deps:
                if dep not in name_map:
                    missing.add(dep)
                    continue
                adjacency[dep].add(name)
                in_degree[name] = in_degree.get(name, 0) + 1

        if missing:
            raise ValueError(f"Unknown dependencies: {', '.join(sorted(missing))}")

        queue = [n for n, deg in in_degree.items() if deg == 0]
        ordered: List[PluginProtocol] = []

        while queue:
            node = queue.pop(0)
            ordered.append(name_map[node])
            for dep in list(adjacency.get(node, set())):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(ordered) != len(plugins_with_meta):
            unresolved = set(name_map) - {p.metadata.name for p in ordered}
            raise ValueError(
                "Circular dependency detected among: " + ", ".join(sorted(unresolved))
            )

        ordered.extend(plugins_without_meta)
        return ordered
