from dash import html, dcc
import dash_bootstrap_components as dbc
from services.upload.validators import ClientSideValidator

class DragDropUploadArea:
    """Simple drag-and-drop upload component with client-side validation."""

    def __init__(self, id: str = "upload-data", *, max_size: int | None = None) -> None:
        self.id = id
        self.max_size = max_size
        self.validator = ClientSideValidator(max_size=max_size)

    def render(self) -> dcc.Upload:
        return dcc.Upload(
            id=self.id,
            max_size=self.max_size,
            multiple=True,
            children=html.Div(
                [
                    html.Span(
                        [
                            html.I(
                                className="fas fa-cloud-upload-alt fa-4x mb-3 text-primary",
                                **{"aria-hidden": "true"},
                            ),
                            html.Span("Upload icon", className="sr-only"),
                        ]
                    ),
                    html.H5("Drag and Drop or Click to Upload", className="text-primary"),
                    html.P(
                        "Supports CSV, Excel (.xlsx, .xls), and JSON files",
                        className="text-muted mb-0",
                    ),
                ]
            ),
            className="file-upload-area",
        )

__all__ = ["DragDropUploadArea"]
