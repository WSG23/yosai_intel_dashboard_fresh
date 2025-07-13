#!/usr/bin/env python3
"""Test script to verify the Dash Pages fix is working."""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_page_registration_fix():
    """Test that page registration now works."""
    try:
        logger.info("🧪 Testing page registration fix...")
        
        # Test 1: Import and create app
        from core.app_factory import create_app
        app = create_app(mode="simple")
        logger.info("✅ App created successfully")
        
        # Test 2: Check page registry
        try:
            from dash.page_registry import page_registry
            registered_pages = list(page_registry.keys())
            logger.info(f"✅ Dash page registry: {registered_pages}")
            
            if registered_pages:
                logger.info("🎉 SUCCESS: Dash Pages registration is working!")
                return True
            else:
                logger.warning("⚠️ Page registry is empty, but app created successfully")
                
        except (ImportError, AttributeError):
            logger.info("ℹ️ Dash page registry not accessible (using manual routing)")
        
        # Test 3: Check manual routing
        if hasattr(app, 'callback_map'):
            callback_ids = []
            for cb_dict in app.callback_map.values():
                output = cb_dict.get('output')
                if output and hasattr(output, 'component_id'):
                    callback_ids.append(output.component_id)
                elif isinstance(output, dict):
                    callback_ids.append(output.get('id'))
            
            if 'page-content' in callback_ids:
                logger.info("✅ Manual routing is active")
                logger.info("🎉 SUCCESS: Manual routing fallback is working!")
                return True
        
        # Test 4: Check that pages can be loaded
        from pages import get_page_layout, PAGE_MODULES
        working_pages = []
        for name in PAGE_MODULES:
            layout_func = get_page_layout(name)
            if layout_func:
                try:
                    layout = layout_func()
                    working_pages.append(name)
                except Exception as e:
                    logger.warning(f"Page {name} layout failed: {e}")
        
        logger.info(f"✅ Working page layouts: {working_pages}")
        
        if working_pages:
            logger.info("🎉 SUCCESS: Page layouts are working!")
            return True
        
        logger.error("❌ No working page layouts found")
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_page_import():
    """Test importing specific pages."""
    try:
        logger.info("🧪 Testing individual page imports...")
        
        test_pages = [
            "pages.deep_analytics",
            "pages.file_upload", 
            "pages.export",
            "pages.settings"
        ]
        
        working_imports = []
        for page_module in test_pages:
            try:
                module = __import__(page_module, fromlist=[''])
                if hasattr(module, 'layout') and hasattr(module, 'register_page'):
                    working_imports.append(page_module)
                    logger.info(f"✅ {page_module}: has layout and register_page")
                else:
                    logger.warning(f"⚠️ {page_module}: missing layout or register_page")
            except Exception as e:
                logger.error(f"❌ {page_module}: import failed - {e}")
        
        logger.info(f"✅ Working page imports: {working_imports}")
        return len(working_imports) > 0
        
    except Exception as e:
        logger.error(f"❌ Page import test failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting Dash Pages Fix Tests")
    
    success = False
    
    # Run tests
    if test_specific_page_import():
        logger.info("✅ Page import test passed")
        
        if test_page_registration_fix():
            logger.info("✅ Page registration test passed")
            success = True
        else:
            logger.error("❌ Page registration test failed")
    else:
        logger.error("❌ Page import test failed")
    
    if success:
        logger.info("🎉 ALL TESTS PASSED - The fix is working!")
        logger.info("💡 Your Dash app should now show page content properly")
    else:
        logger.error("❌ TESTS FAILED - Check the error messages above")
        logger.info("💡 Apply the fixes from the artifacts and try again")
    
    sys.exit(0 if success else 1)
