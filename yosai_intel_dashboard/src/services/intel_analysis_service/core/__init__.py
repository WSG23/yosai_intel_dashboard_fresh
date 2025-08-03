"""Core modules for intel analysis service.

Provides ETL pipeline, entity resolution, versioning, and streaming utilities.
"""

from .graph_entity_resolution import EntityResolver
from .graph_etl_pipeline import GraphETLPipeline
from .graph_versioning import GraphVersioner
from .streaming import KafkaETLConsumer

__all__ = [
    "GraphETLPipeline",
    "EntityResolver",
    "GraphVersioner",
    "KafkaETLConsumer",
]
