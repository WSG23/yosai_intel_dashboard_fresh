from pages import file_upload
from tests.stubs.services.upload.controllers.upload_controller import (
    UnifiedUploadController,
)
from tests.stubs.services.upload.upload_queue_manager import UploadQueueManager


def test_file_upload_page_loader():
    page = file_upload.load_page(
        controller=UnifiedUploadController(), queue_manager=UploadQueueManager()
    )
    assert callable(page.layout)
    assert callable(page.register_callbacks)
