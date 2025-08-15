from __future__ import annotations

from src.infrastructure.monitoring.visualization import drift_chart


def test_drift_chart_provides_shareable_link_and_annotations():
    viz = drift_chart([1, 2, 3])
    assert viz.shareable_link.startswith("/export/")
    assert "<iframe" in viz.embed_code

    before = viz.version
    viz.annotate("note")
    assert viz.version == before + 1
    assert viz.annotations[-1] == "note"
