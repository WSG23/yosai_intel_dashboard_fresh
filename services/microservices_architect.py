from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ServiceBoundary:
    """Represents a candidate microservice boundary."""

    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)


class MicroservicesArchitect:
    """Utility class for microservice decomposition planning."""

    def __init__(self, modules: Dict[str, Any] | None = None) -> None:
        # Existing modules or other context objects can be passed in.
        self.modules = modules or {}

    def analyze_domain(self) -> List[ServiceBoundary]:
        """Analyze modules and derive initial service boundaries.

        This is a placeholder implementation that simply maps each
        module name to a :class:`ServiceBoundary` with a basic description.
        """
        boundaries = []
        for name in self.modules:
            boundaries.append(
                ServiceBoundary(
                    name=name,
                    description=f"Service boundary generated for {name}",
                )
            )
        return boundaries

    def evaluate_dependencies(self, boundaries: List[ServiceBoundary]) -> None:
        """Evaluate coupling between boundaries.

        Dependencies are currently mocked by relating each boundary to the
        next one alphabetically. The resulting list is assigned to the
        ``dependencies`` field of each boundary.
        """
        names = sorted(boundary.name for boundary in boundaries)
        name_to_next = {
            name: names[i + 1] if i + 1 < len(names) else None
            for i, name in enumerate(names)
        }
        for boundary in boundaries:
            next_name = name_to_next.get(boundary.name)
            if next_name:
                boundary.dependencies = [next_name]

    def generate_microservices_roadmap(self) -> Dict[str, Any]:
        """Produce a minimal roadmap for microservice extraction."""
        boundaries = self.analyze_domain()
        self.evaluate_dependencies(boundaries)

        phases = [
            {
                "name": "Identification",
                "description": "Analyze domain and outline candidate boundaries",
            },
            {
                "name": "Decomposition",
                "description": "Iteratively extract and deploy services",
            },
        ]

        return {
            "boundaries": [boundary.__dict__ for boundary in boundaries],
            "phases": phases,
        }
