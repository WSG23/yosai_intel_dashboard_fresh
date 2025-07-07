#!/usr/bin/env python3
"""Simple test to verify upload is working"""


def test_import():
    """Test that the page imports correctly."""
    import pages.file_upload as upload_page
    layout = upload_page.layout()
    health = upload_page.check_upload_system_health()
    assert health["status"] == "healthy"
    print("✅ Upload page imports and layout is generated successfully")

if __name__ == "__main__":
    test_import()
    print("\n🎉 Upload system is working!")
    print("Start your app and test the upload page.")
