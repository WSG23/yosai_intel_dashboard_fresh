"""Simple heuristics for deriving microservice boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List


@dataclass
class ServiceBoundary:
    """Represents a candidate microservice boundary."""

    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)


class MicroservicesArchitect:
    """Utility class for microservice decomposition planning."""

    SERVICE_KEYWORDS: Dict[str, str] = {
        "upload": "Upload Service",
        "analytics": "Analytics Service",
        "security": "Security Service",
        "stream": "Streaming Service",
        "learning": "Learning Service",
    }

    DEFAULT_DEPENDENCIES: Dict[str, List[str]] = {
        "Security Service": ["Core Service"],
        "Upload Service": ["Security Service", "Core Service"],
        "Analytics Service": ["Upload Service", "Core Service"],
        "Streaming Service": ["Upload Service"],
        "Learning Service": ["Analytics Service"],
    }

    def __init__(
        self,
        modules: Dict[str, Any] | None = None,
        services_root: str | Path | None = None,
    ) -> None:
        # Existing modules or other context objects can be passed in.
        self.modules = modules or {}
        self.services_root = Path(services_root or Path(__file__).resolve().parent)

    def analyze_domain(self) -> List[ServiceBoundary]:
        """Analyze modules and derive initial service boundaries.

        When ``self.modules`` is provided it will be used directly.  Otherwise
        the ``services`` package is scanned and grouped into boundaries based
        on simple keyword heuristics.
        """

        if self.modules:
            service_map = {
                self._determine_boundary(name): [name] for name in self.modules
            }
        else:
            service_map = self._discover_service_modules()

        boundaries: List[ServiceBoundary] = []
        for boundary_name, modules in service_map.items():
            description = "Modules: " + ", ".join(sorted(modules))
            boundaries.append(
                ServiceBoundary(name=boundary_name, description=description)
            )

        return boundaries

    def evaluate_dependencies(self, boundaries: List[ServiceBoundary]) -> None:
        """Evaluate coupling between boundaries.

        Dependencies are currently mocked by relating each boundary to the
        next one alphabetically. The resulting list is assigned to the
        ``dependencies`` field of each boundary.
        """
        available = {b.name for b in boundaries}
        for boundary in boundaries:
            deps = self.DEFAULT_DEPENDENCIES.get(boundary.name, [])
            boundary.dependencies = [d for d in deps if d in available]

    # ------------------------------------------------------------------
    # Internal helper methods
    # ------------------------------------------------------------------

    def _discover_service_modules(self) -> Dict[str, List[str]]:
        """Scan the services package and group files into boundaries."""
        mapping: Dict[str, List[str]] = {}
        for path in self.services_root.iterdir():
            if path.name.startswith("__"):
                continue
            if path.name == Path(__file__).name:
                continue

            if path.is_dir():
                key = self._determine_boundary(path.name)
                mapping.setdefault(key, []).append(path.name)
            elif path.suffix == ".py":
                key = self._determine_boundary(path.stem)
                mapping.setdefault(key, []).append(path.stem)
        return mapping

    def _determine_boundary(self, name: str) -> str:
        lower = name.lower()
        for keyword, boundary in self.SERVICE_KEYWORDS.items():
            if keyword in lower:
                return boundary
        return "Core Service"

    def generate_microservices_roadmap(self) -> Dict[str, Any]:
        """Produce a minimal roadmap for microservice extraction."""
        boundaries = self.analyze_domain()
        self.evaluate_dependencies(boundaries)

        phases = [
            {
                "name": "Assessment",
                "description": "Enumerate modules and categorize responsibilities",
            },
            {
                "name": "Design",
                "description": "Define APIs and contracts for each service",
            },
            {
                "name": "Extraction",
                "description": "Split services and create integration points",
            },
            {
                "name": "Deployment",
                "description": "Gradually deploy and monitor independent services",
            },
        ]

        return {
            "boundaries": [boundary.__dict__ for boundary in boundaries],
            "phases": phases,
        }
