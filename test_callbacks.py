#!/usr/bin/env python3
"""
Test to verify callback registration is working
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure new deep_analytics package can be imported
import pages.deep_analytics.layout as deep_layout

def test_callback_registration():
    """Test that callbacks are properly registered"""
    
    try:
        # Import the app factory
        from core.app_factory import create_app
        
        logger.info("Creating app...")
        app = create_app()
        
        # Check if app has callbacks
        if hasattr(app, 'callback_map'):
            callback_count = len(app.callback_map)
            logger.info(f"✅ App created with {callback_count} callbacks registered")
            
            # List callback IDs for debugging
            for callback_id in app.callback_map.keys():
                logger.info(f"  - Callback: {callback_id}")
                
            # Check specifically for upload callback
            upload_callbacks = [cid for cid in app.callback_map.keys() 
                              if 'upload' in cid.lower()]
            
            if upload_callbacks:
                logger.info(f"✅ Found {len(upload_callbacks)} upload-related callbacks")
                for ucb in upload_callbacks:
                    logger.info(f"  - Upload callback: {ucb}")
            else:
                logger.warning("❌ No upload callbacks found!")
                
            # Test for specific callback outputs we expect
            expected_outputs = [
                'upload-results.children',
                'file-preview.children', 
                'upload-nav.children'
            ]
            
            found_outputs = []
            for expected in expected_outputs:
                for callback_id in app.callback_map.keys():
                    if expected in callback_id:
                        found_outputs.append(expected)
                        break
            
            logger.info(f"Expected outputs found: {found_outputs}")
            missing_outputs = set(expected_outputs) - set(found_outputs)
            if missing_outputs:
                logger.warning(f"Missing expected outputs: {missing_outputs}")
            else:
                logger.info("✅ All expected upload outputs found!")
                
        else:
            logger.error("❌ App has no callback_map attribute")
            
        return app
        
    except Exception as e:
        logger.error(f"❌ Failed to create app: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_upload_module():
    """Test that upload module can be imported and has callbacks"""
    
    try:
        logger.info("Testing upload module import...")
        import pages.file_upload
        
        # Check if module has the callback registration function
        if hasattr(pages.file_upload, 'register_upload_callbacks'):
            logger.info("✅ Upload module has register_upload_callbacks function")
        else:
            logger.warning("❌ Upload module missing register_upload_callbacks")
            
        # Check if module has the callback function
        if hasattr(pages.file_upload, 'consolidated_upload_callback'):
            logger.info("✅ Upload module has consolidated_upload_callback function")
        else:
            logger.warning("❌ Upload module missing consolidated_upload_callback")
            
        # List all attributes for debugging
        attrs = [attr for attr in dir(pages.file_upload) if not attr.startswith('_')]
        logger.info(f"Upload module attributes: {attrs}")
        
    except Exception as e:
        logger.error(f"❌ Failed to import upload module: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("🧪 Testing callback registration...")
    logger.info("=" * 50)
    
    # Test 1: Upload module import
    test_upload_module()
    logger.info("-" * 30)
    
    # Test 2: App creation and callback registration
    app = test_callback_registration()
    
    if app:
        logger.info("✅ All tests passed! Upload should work.")
        logger.info("\n📋 Next steps:")
        logger.info("1. Run: python3 test_upload.py  (to create test file)")
        logger.info("2. Run: python3 app.py  (to start the app)")
        logger.info("3. Go to: http://127.0.0.1:8050/upload")
        logger.info("4. Test file upload functionality")
    else:
        logger.info("❌ Tests failed. Check the errors above.")
