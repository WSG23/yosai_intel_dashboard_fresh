from __future__ import annotations

from typing import Any, Dict, List


class APIGatewayArchitect:
    """Plan the API gateway and service mesh configuration."""

    def design_api_gateway(
        self, service_boundaries: Dict[str, List[str]]
    ) -> Dict[str, Dict[str, Any]]:
        """Create a gateway plan for the provided services."""
        routing = self._create_routing(service_boundaries)
        security = self._create_security_policies(service_boundaries)
        observability = self._create_observability_hooks(service_boundaries)
        return {
            "routing": routing,
            "security": security,
            "observability": observability,
        }

    def design_service_mesh(self, services: List[str]) -> Dict[str, Any]:
        """Return a skeleton service mesh configuration.

        Parameters
        ----------
        services:
            A list of service names that should participate in the mesh.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing three keys:
            ``service_entries`` for basic service definitions,
            ``traffic_policies`` describing default routing behaviour and
            ``observability`` for metrics and tracing configuration.
        """

        service_entries = [{"name": name} for name in services]

        traffic_policies = [
            {
                "destination": name,
                "policy": {"retries": 3, "timeout": "5s"},
            }
            for name in services
        ]

        observability = {"tracing": True, "metrics": True}

        return {
            "service_entries": service_entries,
            "traffic_policies": traffic_policies,
            "observability": observability,
        }

    # ------------------------------------------------------------------
    def _create_routing(
        self, service_boundaries: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Stub for dynamic routing configuration."""
        routes = [
            {"service": service, "paths": paths}
            for service, paths in service_boundaries.items()
        ]
        return {"rules": routes}

    def _create_security_policies(
        self, service_boundaries: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Stub for gateway security policies."""
        return {"policies": []}

    def _create_observability_hooks(
        self, service_boundaries: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Stub for metrics and tracing integration."""
        return {"hooks": []}


__all__ = ["APIGatewayArchitect"]
