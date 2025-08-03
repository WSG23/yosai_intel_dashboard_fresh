from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from core.graph_etl_pipeline import GraphETLPipeline  # noqa: E402


def test_pipeline_generates_versioned_snapshot():
    pipeline = GraphETLPipeline()
    logs = ["2024-01-01T00:00:00Z,alice,bob,LOGIN"]
    snapshot = pipeline.process_logs(logs)
    assert snapshot["nodes"][0]["version"] == 1
    assert snapshot["edges"][0]["version"] == 1
