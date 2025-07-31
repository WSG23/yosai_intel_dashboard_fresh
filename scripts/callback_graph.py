#!/usr/bin/env python3
"""Generate a GraphViz diagram of registered Dash callbacks."""

from __future__ import annotations

import os

from dash import Dash
from graphviz import Digraph

from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.services.upload.callbacks import UploadCallbacks


def load_callbacks() -> TrulyUnifiedCallbacks:
    """Create app, register callbacks and return coordinator."""
    app = Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)
    coord.register_all_callbacks(UploadCallbacks)
    return coord


def build_graph(coord: TrulyUnifiedCallbacks) -> Digraph:
    """Return GraphViz digraph representing callback dependencies."""
    graph = Digraph(comment="Callback Graph")

    for reg in coord.registered_callbacks.values():
        for out in reg.outputs:
            out_id = f"{out.component_id}.{out.component_property}"
            for inp in reg.inputs:
                in_id = f"{inp.component_id}.{inp.component_property}"
                graph.edge(out_id, in_id)
    return graph


def main() -> None:
    coord = load_callbacks()
    graph = build_graph(coord)

    docs_dir = os.path.join(os.path.dirname(__file__), os.pardir, "docs")
    docs_dir = os.path.abspath(docs_dir)
    os.makedirs(docs_dir, exist_ok=True)

    dot_path = os.path.join(docs_dir, "callback_graph.dot")
    with open(dot_path, "w") as f:
        f.write(graph.source)

    graph.render(os.path.join(docs_dir, "callback_graph"), format="png", cleanup=True)
    print(f"Wrote {dot_path} and callback_graph.png")


if __name__ == "__main__":
    main()
