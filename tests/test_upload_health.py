from pages import file_upload

def test_check_upload_system_health():
    result = file_upload.check_upload_system_health()
    assert result["status"] == "healthy"
    assert isinstance(result["errors"], list)
