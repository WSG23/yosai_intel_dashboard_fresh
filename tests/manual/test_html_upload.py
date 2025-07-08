#!/usr/bin/env python3
"""Test the HTML-based upload fix"""

def test_html_upload():
    try:
        import pages.file_upload as upload_page
        print("✅ Upload page imports successfully")

        layout = upload_page.layout()
        print("✅ HTML layout creates successfully")

        layout_str = str(layout)
        if 'drag-drop-upload' in layout_str and 'upload-progress' in layout_str:
            print("✅ Upload components found in layout")
        else:
            print("❌ Upload components missing from layout")
            return False

        health = upload_page.check_upload_system_health()
        print(f"✅ Health check: {health['status']}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_html_upload()
    if success:
        print("\n🎉 HTML upload system is working!")
        print("Start your app - you should see the upload area.")
    else:
        print("\n❌ HTML upload system has issues.")
