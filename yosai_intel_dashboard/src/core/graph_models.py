"""Data models for graph mutations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class NodeMutation:
    """Represents a mutation to a graph node."""

    node_id: str
    properties: Dict[str, Any]
    version: int = 0


@dataclass
class EdgeMutation:
    """Represents a mutation to a graph edge."""

    source: str
    target: str
    properties: Dict[str, Any]
    version: int = 0


__all__ = ["NodeMutation", "EdgeMutation"]

