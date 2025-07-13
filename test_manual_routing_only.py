#!/usr/bin/env python3
"""Test manual routing without Dash Pages."""

import os
os.environ['DB_PASSWORD'] = 'test_password'

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_manual_routing():
    try:
        from core.app_factory import create_app
        logger.info("🧪 Testing manual routing only...")
        
        app = create_app(mode="simple")
        logger.info("✅ App created successfully")
        
        # Check if manual routing callback exists
        if hasattr(app, 'callback_map'):
            callback_outputs = []
            for cb in app.callback_map.values():
                output = cb.get('output')
                if output:
                    if hasattr(output, 'component_id'):
                        callback_outputs.append(output.component_id)
                    elif isinstance(output, dict):
                        callback_outputs.append(output.get('id'))
            
            if 'page-content' in callback_outputs:
                logger.info("✅ Manual routing callback found")
                return True
            else:
                logger.warning(f"⚠️ Manual routing not found. Callbacks: {callback_outputs}")
        
        # Test page layout functions
        from pages import get_page_layout
        test_pages = ['deep_analytics', 'file_upload', 'export', 'settings']
        working = []
        
        for page in test_pages:
            layout_func = get_page_layout(page)
            if layout_func:
                try:
                    layout_func()  # Test that it can be called
                    working.append(page)
                except Exception as e:
                    logger.warning(f"⚠️ {page} layout error: {e}")
            else:
                logger.warning(f"⚠️ No layout function for {page}")
        
        logger.info(f"✅ Working layouts: {working}")
        return len(working) > 0
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_manual_routing():
        logger.info("🎉 Manual routing test PASSED")
    else:
        logger.error("❌ Manual routing test FAILED")
