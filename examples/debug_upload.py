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
    logger.info("🔍 Testing imports...")
    
    try:
        import dash
        logger.info(f"✅ Dash version: {dash.__version__}")
    except ImportError as e:
        logger.info(f"❌ Dash import failed: {e}")
        return False
    
    try:
        import dash_bootstrap_components as dbc
        logger.info("✅ Dash Bootstrap Components imported")
    except ImportError as e:
        logger.info(f"❌ DBC import failed: {e}")
        return False
    
    try:
        import pandas as pd
        logger.info(f"✅ Pandas version: {pd.__version__}")
    except ImportError as e:
        logger.info(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        from config.config import get_config
        config = get_config()
        logger.info("✅ Config system working")
    except Exception as e:
        logger.info(f"❌ Config import failed: {e}")
        return False
    
    return True

def debug_file_upload_module():
    """Test file upload module"""
    logger.info("\n🔍 Testing file upload module...")
    
    try:
        import pages.file_upload as fu
        logger.info("✅ File upload module imported")
        
        # Check required functions
        required_functions = [
            'layout', 'register_upload_callbacks', 'get_uploaded_data',
            'consolidated_upload_callback', 'save_confirmed_device_mappings_callback'
        ]
        
        for func_name in required_functions:
            if hasattr(fu, func_name):
                logger.info(f"✅ Function '{func_name}' found")
            else:
                logger.info(f"❌ Function '{func_name}' missing")
                
        return True
        
    except Exception as e:
        logger.info(f"❌ File upload module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_analytics_module():
    """Test analytics module for conflicts"""
    logger.info("\n🔍 Testing analytics module...")
    
    try:
        import pages.deep_analytics as da
        logger.info("✅ Deep analytics module imported")
        
        # Check for required functions
        if hasattr(da, 'layout'):
            logger.info("✅ Analytics layout function found")
        else:
            logger.info("❌ Analytics layout function missing")
            
        if hasattr(da, 'handle_analysis_buttons'):
            logger.info("✅ Analytics callback function found")
        else:
            logger.info("❌ Analytics callback function missing")
            
        return True
        
    except Exception as e:
        logger.info(f"❌ Analytics module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_app_creation():
    """Test app creation and callback registration"""
    logger.info("\n🔍 Testing app creation...")
    
    try:
        from core.app_factory import create_app
        app = create_app()
        logger.info("✅ App created successfully")
        
        # Check callback registration
        if hasattr(app, 'callback_map'):
            callback_count = len(app.callback_map)
            logger.info(f"✅ {callback_count} callbacks registered")
            
            # List all callbacks
            logger.info("\n📋 Registered callbacks:")
            for i, callback_id in enumerate(app.callback_map.keys(), 1):
                logger.info(f"  {i}. {callback_id}")
            
            # Check for upload-related callbacks
            upload_callbacks = [cid for cid in app.callback_map.keys() 
                              if any(term in cid.lower() for term in ['upload', 'file', 'preview'])]
            
            if upload_callbacks:
                logger.info(f"\n✅ {len(upload_callbacks)} upload callbacks found:")
                for ucb in upload_callbacks:
                    logger.info(f"  - {ucb}")
            else:
                logger.info("\n❌ No upload callbacks found!")
                
            # Check for duplicate analytics callbacks
            analytics_callbacks = [cid for cid in app.callback_map.keys() 
                                 if 'analytics-display-area' in cid]
            
            if len(analytics_callbacks) > 1:
                logger.info(f"\n❌ Duplicate analytics callbacks found: {analytics_callbacks}")
            elif len(analytics_callbacks) == 1:
                logger.info(f"\n✅ Single analytics callback found: {analytics_callbacks[0]}")
            else:
                logger.info("\n⚠️ No analytics callbacks found")
                
            return True
        else:
            logger.info("❌ App has no callback_map")
            return False
            
    except Exception as e:
        logger.info(f"❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_file_processor():
    """Test file processing"""
    logger.info("\n🔍 Testing file processor...")
    
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
            logger.info("✅ File processing works")
            df = result['data']
            logger.info(f"  - Rows: {len(df)}")
            logger.info(f"  - Columns: {list(df.columns)}")
        else:
            logger.info(f"❌ File processing failed: {result.get('error')}")
            
        return result.get('success', False)
        
    except Exception as e:
        logger.info(f"❌ File processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_full_debug():
    """Run all debug tests"""
    logger.info("🚀 FULL UPLOAD DEBUG TEST")
    logger.info("=" * 50)
    
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
            logger.info(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
        logger.info("-" * 30)
    
    # Summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info("=" * 30)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED!")
        logger.info("Upload functionality should work properly.")
        logger.info("\n📋 Next steps:")
        logger.info("1. Run: python3 test_upload.py  (create test file)")
        logger.info("2. Run: python3 app.py  (start app)")
        logger.info("3. Go to: http://127.0.0.1:8050/upload")
        logger.info("4. Upload the test file and check logs")
    else:
        logger.info("\n⚠️ SOME TESTS FAILED")
        logger.info("Check the errors above and fix them before testing upload.")
    
    return passed == total

if __name__ == "__main__":
    run_full_debug()