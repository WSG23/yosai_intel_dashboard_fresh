#!/usr/bin/env python3
"""Test individual page layout functions directly"""

import sys
import logging
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_individual_layouts() -> Dict[str, Any]:
    """Test each page layout function directly to isolate issues."""
    results = {}
    
    # Test Export Page
    try:
        from pages.export import layout as export_layout
        content = export_layout()
        results['export'] = {
            'status': 'SUCCESS',
            'type': type(content).__name__,
            'content_check': hasattr(content, 'children') if hasattr(content, 'children') else 'No children attr'
        }
        logger.info(f"✅ Export layout works: {type(content)}")
    except Exception as e:
        results['export'] = {'status': 'FAILED', 'error': str(e)}
        logger.error(f"❌ Export layout failed: {e}")

    # Test Settings Page  
    try:
        from pages.settings import layout as settings_layout
        content = settings_layout()
        results['settings'] = {
            'status': 'SUCCESS',
            'type': type(content).__name__,
            'content_check': hasattr(content, 'children') if hasattr(content, 'children') else 'No children attr'
        }
        logger.info(f"✅ Settings layout works: {type(content)}")
    except Exception as e:
        results['settings'] = {'status': 'FAILED', 'error': str(e)}
        logger.error(f"❌ Settings layout failed: {e}")

    # Test File Upload Page (uses class-based approach)
    try:
        from pages.file_upload import layout as upload_layout
        content = upload_layout()
        results['file_upload'] = {
            'status': 'SUCCESS', 
            'type': type(content).__name__,
            'content_check': hasattr(content, 'children') if hasattr(content, 'children') else 'No children attr'
        }
        logger.info(f"✅ Upload layout works: {type(content)}")
    except Exception as e:
        results['file_upload'] = {'status': 'FAILED', 'error': str(e)}
        logger.error(f"❌ Upload layout failed: {e}")

    # Test Deep Analytics Page  
    try:
        from pages.deep_analytics import layout as analytics_layout
        content = analytics_layout()
        results['deep_analytics'] = {
            'status': 'SUCCESS',
            'type': type(content).__name__, 
            'content_check': hasattr(content, 'children') if hasattr(content, 'children') else 'No children attr'
        }
        logger.info(f"✅ Analytics layout works: {type(content)}")
    except Exception as e:
        results['deep_analytics'] = {'status': 'FAILED', 'error': str(e)}
        logger.error(f"❌ Analytics layout failed: {e}")

    # Test Graphs Page
    try:
        from pages.graphs import layout as graphs_layout
        content = graphs_layout()
        results['graphs'] = {
            'status': 'SUCCESS',
            'type': type(content).__name__,
            'content_check': hasattr(content, 'children') if hasattr(content, 'children') else 'No children attr'
        }
        logger.info(f"✅ Graphs layout works: {type(content)}")
    except Exception as e:
        results['graphs'] = {'status': 'FAILED', 'error': str(e)}
        logger.error(f"❌ Graphs layout failed: {e}")

    return results

def test_page_registration() -> Dict[str, Any]:
    """Test if pages can register with Dash properly."""
    reg_results = {}
    
    # Test page registration functions
    try:
        from pages.export import register_page as export_register
        export_register()
        reg_results['export_register'] = {'status': 'SUCCESS'}
        logger.info("✅ Export page registration works")
    except Exception as e:
        reg_results['export_register'] = {'status': 'FAILED', 'error': str(e)}
        logger.error(f"❌ Export registration failed: {e}")

    try:
        from pages.settings import register_page as settings_register  
        settings_register()
        reg_results['settings_register'] = {'status': 'SUCCESS'}
        logger.info("✅ Settings page registration works")
    except Exception as e:
        reg_results['settings_register'] = {'status': 'FAILED', 'error': str(e)}
        logger.error(f"❌ Settings registration failed: {e}")

    try:
        from pages.file_upload import register_page as upload_register
        upload_register() 
        reg_results['upload_register'] = {'status': 'SUCCESS'}
        logger.info("✅ Upload page registration works")
    except Exception as e:
        reg_results['upload_register'] = {'status': 'FAILED', 'error': str(e)}
        logger.error(f"❌ Upload registration failed: {e}")

    return reg_results

if __name__ == '__main__':
    print("🔍 Testing individual page layouts...")
    
    layout_results = test_individual_layouts()
    print(f"\n📊 Layout Test Results:")
    for page, result in layout_results.items():
        status = result['status']
        emoji = "✅" if status == 'SUCCESS' else "❌"
        print(f"{emoji} {page}: {result}")
    
    print(f"\n🔍 Testing page registration...")
    reg_results = test_page_registration()
    print(f"\n📊 Registration Test Results:")
    for page, result in reg_results.items():
        status = result['status'] 
        emoji = "✅" if status == 'SUCCESS' else "❌"
        print(f"{emoji} {page}: {result}")
    
    # Summary
    layout_success = sum(1 for r in layout_results.values() if r['status'] == 'SUCCESS')
    reg_success = sum(1 for r in reg_results.values() if r['status'] == 'SUCCESS')
    
    print(f"\n📈 SUMMARY:")
    print(f"Layout tests: {layout_success}/{len(layout_results)} passed")
    print(f"Registration tests: {reg_success}/{len(reg_results)} passed")
    
    if layout_success == len(layout_results):
        print("✅ All layouts work - issue is likely with Dash Pages navigation")
    else:
        print("❌ Some layouts broken - fix individual pages first")
