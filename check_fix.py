#!/usr/bin/env python3
"""Check if all fixes are working"""

import os
import sys

def test_imports():
    """Test critical imports"""
    print("🔍 Testing imports...")
    
    try:
        from dash import register_page as dash_register_page
        print("✅ dash_register_page import works")
    except Exception as e:
        print(f"❌ dash_register_page import failed: {e}")
        return False
    
    try:
        import pages.file_upload
        print("✅ pages.file_upload imports")
    except Exception as e:
        print(f"❌ pages.file_upload failed: {e}")
        return False
    
    try:
        import pages.export
        print("✅ pages.export imports")
    except Exception as e:
        print(f"❌ pages.export failed: {e}")
        return False
    
    return True

def test_layouts():
    """Test page layouts"""
    print("\n🔍 Testing layouts...")
    
    try:
        import pages.file_upload
        layout = pages.file_upload.layout()
        print("✅ file_upload layout works")
    except Exception as e:
        print(f"❌ file_upload layout failed: {e}")
        return False
    
    try:
        import pages.export
        layout = pages.export.layout()
        print("✅ export layout works")
    except Exception as e:
        print(f"❌ export layout failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    print("\n🔍 Testing environment...")
    
    db_pass = os.getenv('DB_PASSWORD')
    if db_pass:
        print("✅ DB_PASSWORD is set")
        return True
    else:
        print("❌ DB_PASSWORD not set - run: export DB_PASSWORD='dev_password'")
        return False

# Run all tests
print("🧪 Testing your fixes...\n")

tests = [
    test_imports(),
    test_layouts(), 
    test_environment(),
]

if all(tests):
    print("\n🎉 ALL TESTS PASSED! Your app should work now.")
    print("Run: python3 app.py")
else:
    print("\n❌ Some tests failed. Check the errors above.")