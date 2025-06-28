#!/usr/bin/env python3
"""
Full debug script to test upload functionality
"""
import sys
import logging
from pathlib import Path

# Add project root to path
# When run from the examples directory, include the repository root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    
    try:
        import dash
        print(f"✅ Dash version: {dash.__version__}")
    except ImportError as e:
        print(f"❌ Dash import failed: {e}")
        return False
    
    try:
        import dash_bootstrap_components as dbc
        print("✅ Dash Bootstrap Components imported")
    except ImportError as e:
        print(f"❌ DBC import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print(f"✅ Pandas version: {pd.__version__}")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        from config.config import get_config
        config = get_config()
        print("✅ Config system working")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    return True

def debug_file_upload_module():
    """Test file upload module"""
    print("\n🔍 Testing file upload module...")
    
    try:
        import pages.file_upload as fu
        print("✅ File upload module imported")
        
        # Check required functions
        required_functions = [
            'layout', 'register_upload_callbacks', 'get_uploaded_data',
            'consolidated_upload_callback', 'save_confirmed_device_mappings_callback'
        ]
        
        for func_name in required_functions:
            if hasattr(fu, func_name):
                print(f"✅ Function '{func_name}' found")
            else:
                print(f"❌ Function '{func_name}' missing")
                
        return True
        
    except Exception as e:
        print(f"❌ File upload module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_analytics_module():
    """Test analytics module for conflicts"""
    print("\n🔍 Testing analytics module...")
    
    try:
        import pages.deep_analytics as da
        print("✅ Deep analytics module imported")
        
        # Check for required functions
        if hasattr(da, 'layout'):
            print("✅ Analytics layout function found")
        else:
            print("❌ Analytics layout function missing")
            
        if hasattr(da, 'handle_analysis_buttons'):
            print("✅ Analytics callback function found")
        else:
            print("❌ Analytics callback function missing")
            
        return True
        
    except Exception as e:
        print(f"❌ Analytics module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_app_creation():
    """Test app creation and callback registration"""
    print("\n🔍 Testing app creation...")
    
    try:
        from core.app_factory import create_app
        app = create_app()
        print("✅ App created successfully")
        
        # Check callback registration
        if hasattr(app, 'callback_map'):
            callback_count = len(app.callback_map)
            print(f"✅ {callback_count} callbacks registered")
            
            # List all callbacks
            print("\n📋 Registered callbacks:")
            for i, callback_id in enumerate(app.callback_map.keys(), 1):
                print(f"  {i}. {callback_id}")
            
            # Check for upload-related callbacks
            upload_callbacks = [cid for cid in app.callback_map.keys() 
                              if any(term in cid.lower() for term in ['upload', 'file', 'preview'])]
            
            if upload_callbacks:
                print(f"\n✅ {len(upload_callbacks)} upload callbacks found:")
                for ucb in upload_callbacks:
                    print(f"  - {ucb}")
            else:
                print("\n❌ No upload callbacks found!")
                
            # Check for duplicate analytics callbacks
            analytics_callbacks = [cid for cid in app.callback_map.keys() 
                                 if 'analytics-display-area' in cid]
            
            if len(analytics_callbacks) > 1:
                print(f"\n❌ Duplicate analytics callbacks found: {analytics_callbacks}")
            elif len(analytics_callbacks) == 1:
                print(f"\n✅ Single analytics callback found: {analytics_callbacks[0]}")
            else:
                print("\n⚠️ No analytics callbacks found")
                
            return True
        else:
            print("❌ App has no callback_map")
            return False
            
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_file_processor():
    """Test file processing"""
    print("\n🔍 Testing file processor...")
    
    try:
        from services.file_processor_service import FileProcessorService
        from services.upload_utils import parse_uploaded_file
        
        # Create a simple test CSV content
        test_csv = "name,value\ntest1,123\ntest2,456"
        import base64
        encoded = base64.b64encode(test_csv.encode('utf-8')).decode('utf-8')
        data_url = f"data:text/csv;base64,{encoded}"
        
        # Test parsing
        result = parse_uploaded_file(data_url, "test.csv")
        
        if result.get('success'):
            print("✅ File processing works")
            df = result['data']
            print(f"  - Rows: {len(df)}")
            print(f"  - Columns: {list(df.columns)}")
        else:
            print(f"❌ File processing failed: {result.get('error')}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ File processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_full_debug():
    """Run all debug tests"""
    print("🚀 FULL UPLOAD DEBUG TEST")
    print("=" * 50)
    
    tests = [
        ("Imports", debug_imports),
        ("File Upload Module", debug_file_upload_module),
        ("Analytics Module", debug_analytics_module),
        ("App Creation", debug_app_creation),
        ("File Processor", debug_file_processor),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
        print("-" * 30)
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 30)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Upload functionality should work properly.")
        print("\n📋 Next steps:")
        print("1. Run: python3 test_upload.py  (create test file)")
        print("2. Run: python3 app.py  (start app)")
        print("3. Go to: http://127.0.0.1:8050/upload")
        print("4. Upload the test file and check logs")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Check the errors above and fix them before testing upload.")
    
    return passed == total

if __name__ == "__main__":
    run_full_debug()