"""Utilities to export graph data to STIX and TAXII."""

from __future__ import annotations

from typing import Dict, Iterable

from analytics.graph_analysis.schema import GraphModel


def export_to_stix(graph: GraphModel) -> Dict:
    """Convert ``graph`` into a minimal STIX bundle.

    The conversion is intentionally lightweight and only includes node ids as
    STIX ``observed-data`` objects.  Real deployments should extend this
    function to include additional properties and relationships.
    """

    objects = [
        {
            "type": "observed-data",
            "id": f"observed-data--{node}",
        }
        for node in graph.graph.nodes()
    ]
    return {"type": "bundle", "objects": objects}


def push_to_taxii(bundle: Dict, collection_url: str) -> None:
    """Push a STIX bundle to a TAXII collection.

    This placeholder uses ``requests`` if available and silently ignores
    errors so the exporter can be used in offline tests.
    """

    try:  # pragma: no cover - network interactions are not tested
        import requests

        requests.post(collection_url, json=bundle, timeout=5)
    except Exception:
        pass
