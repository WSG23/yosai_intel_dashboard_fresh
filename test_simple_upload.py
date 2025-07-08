#!/usr/bin/env python3
"""Test the simple upload page"""


def test_simple_layout():
    try:
        import pages.file_upload as upload_page
        print("✅ Upload page imports")
        
        layout = upload_page.layout()
        print("✅ Layout created")
        
        # Check layout contains upload component
        layout_str = str(layout)
        if 'drag-drop-upload' in layout_str:
            print("✅ Upload component found")
        else:
            print("❌ Upload component missing")
            return False

        if 'Upload Data Files' in layout_str:
            print("✅ Upload header found")
        else:
            print("❌ Upload header missing")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_layout()
    if success:
        print("\n🎉 Simple upload page should work!")
    else:
        print("\n❌ Issues found.")
