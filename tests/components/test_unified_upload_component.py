from dash import dcc

from components.upload import UnifiedUploadComponent


class DummyManager:
    def __init__(self) -> None:
        self.ids = []

    def register_handler(self, *_, callback_id=None, **__):
        self.ids.append(callback_id)

        def decorator(func):
            return func

        return decorator


def test_find_upload_components():
    comp = UnifiedUploadComponent()
    from components.upload.unified_upload_component import _find_upload_components

    layout = comp.layout()
    uploads = _find_upload_components(layout)
    assert uploads
    assert all(isinstance(u, dcc.Upload) for u in uploads)


def test_validate_component_state():
    comp = UnifiedUploadComponent()
    mgr = DummyManager()
    assert comp.validate_component_state(mgr)
    assert {
        "file_upload_handle",
        "file_upload_progress",
        "file_upload_finalize",
    }.issubset(set(mgr.ids))
