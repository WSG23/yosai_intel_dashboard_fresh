from __future__ import annotations

import base64
import io
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Protocol

# External libraries used only for demonstration; they are optional at runtime.
import matplotlib.pyplot as plt


class FigureProtocol(Protocol):
    def savefig(self, buf: io.BytesIO, format: str) -> None: ...


@dataclass
class ExportedView:
    """Simple container for exported visualization data."""

    content: bytes | str
    format: str
    annotations: List[str] = field(default_factory=list)
    version: int = 1


class ExportService:
    """Service capable of exporting matplotlib figures to multiple formats.

    The service keeps exported views in memory so tests can access the stored
    content via a generated shareable link.  It also supports collaborative
    annotations which bump the view version on each update.
    """

    def __init__(self) -> None:
        self._views: Dict[str, ExportedView] = {}

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------
    def _save_image(self, fig: FigureProtocol, fmt: str) -> bytes:
        buf = io.BytesIO()
        fig.savefig(buf, format=fmt)
        buf.seek(0)
        return buf.read()

    def _save_html(self, fig: FigureProtocol) -> str:
        image = self._save_image(fig, "png")
        b64 = base64.b64encode(image).decode("ascii")
        return f"<html><body><img src='data:image/png;base64,{b64}'/></body></html>"

    def export(self, fig: FigureProtocol, fmt: str) -> bytes | str:
        fmt = fmt.lower()
        if fmt in {"svg", "png", "jpeg", "jpg", "pdf"}:
            return self._save_image(fig, fmt)
        if fmt == "html":
            return self._save_html(fig)
        raise ValueError(f"unsupported format: {fmt}")

    # ------------------------------------------------------------------
    # Shareable links and annotations
    # ------------------------------------------------------------------
    def create_shareable(self, fig: FigureProtocol, fmt: str) -> tuple[str, str, str]:
        """Export ``fig`` and return (id, link, embed code)."""

        content = self.export(fig, fmt)
        view_id = str(uuid.uuid4())
        self._views[view_id] = ExportedView(content=content, format=fmt)
        link = f"/export/{view_id}"
        embed = f"<iframe src='{link}'></iframe>"
        return view_id, link, embed

    def add_annotation(self, view_id: str, note: str) -> ExportedView:
        view = self._views[view_id]
        view.annotations.append(note)
        view.version += 1
        return view

    def get_view(self, view_id: str) -> ExportedView:
        return self._views[view_id]
