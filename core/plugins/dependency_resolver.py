from __future__ import annotations

from typing import DefaultDict, Dict, List, Set

from core.protocols.plugin import PluginProtocol


class CircularDependencyError(ValueError):
    """Raised when a dependency cycle is detected."""

    def __init__(self, nodes: Iterable[str]):
        self.nodes = list(nodes)
        super().__init__(
            "Circular dependency detected among: " + ", ".join(sorted(self.nodes))
        )


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
            raise CircularDependencyError(unresolved)

        ordered.extend(plugins_without_meta)
        return ordered

    def _find_cycle(
        self, adjacency: Dict[str, Set[str]], nodes: Set[str]
    ) -> List[str]:  # pragma: no cover - heuristic, optional
        visited: Set[str] = set()
        stack: List[str] = []

        def dfs(node: str) -> List[str]:
            if node in stack:
                idx = stack.index(node)
                return stack[idx:] + [node]
            if node in visited:
                return []
            visited.add(node)
            stack.append(node)
            for nxt in adjacency.get(node, set()):
                if nxt not in nodes:
                    continue
                cycle = dfs(nxt)
                if cycle:
                    return cycle
            stack.pop()
            return []

        for n in nodes:
            cycle = dfs(n)
            if cycle:
                return cycle
        return []
