from __future__ import annotations

from dash import dcc

from components.file_upload_component import FileUploadComponent


def _find_upload_components(component) -> list[dcc.Upload]:
    """Recursively collect any ``dcc.Upload`` components."""

    found: list[dcc.Upload] = []
    if isinstance(component, dcc.Upload):
        found.append(component)

    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            found.extend(_find_upload_components(child))
    elif children is not None:
        found.extend(_find_upload_components(children))

    return found


class UnifiedUploadComponent(FileUploadComponent):
    """Unified upload component wrapping :class:`FileUploadComponent`."""

    def validate_component_state(self, manager=None) -> bool:
        """Verify required attributes and callback registration."""

        required = ["callback_manager", "layout", "register_callbacks"]
        if any(not hasattr(self, attr) for attr in required):
            return False

        try:
            layout = self.layout()
        except Exception:
            return False

        uploads = _find_upload_components(layout)
        if not uploads:
            return False

        class DummyManager:
            def __init__(self) -> None:
                self.ids: list[str] = []

            def register_handler(self, *_, callback_id=None, **__):  # type: ignore[override]
                self.ids.append(callback_id)

                def decorator(func):
                    return func

                return decorator

        mgr = manager or DummyManager()

        try:
            self.register_callbacks(mgr)
        except Exception:
            return False

        expected = {
            "file_upload_handle",
            "file_upload_progress",
            "file_upload_finalize",
        }

        ids = getattr(mgr, "ids", [])
        return expected.issubset(set(ids))


__all__ = ["UnifiedUploadComponent"]
