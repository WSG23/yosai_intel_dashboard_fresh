#!/usr/bin/env python3
"""Diagnosis script for the main project's Dash Pages setup"""

import sys
import logging
from typing import Dict, Any

# Configure logging  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose_page_registry() -> Dict[str, Any]:
    """Check the project's page registration system."""
    results = {}
    
    try:
        from pages import get_available_pages, PAGE_MODULES
        
        # Check available pages
        available = get_available_pages()
        results['available_pages'] = available
        results['total_pages'] = len(PAGE_MODULES)
        results['working_pages'] = sum(available.values())
        
        logger.info(f"📊 Page status: {results['working_pages']}/{results['total_pages']} working")
        for page, status in available.items():
            emoji = "✅" if status else "❌"
            logger.info(f"  {emoji} {page}")
            
    except Exception as e:
        results['page_registry_error'] = str(e)
        logger.error(f"❌ Page registry check failed: {e}")
    
    return results

def diagnose_dash_app() -> Dict[str, Any]:
    """Try to create the main app and check its state."""
    results = {}
    
    try:
        # Try importing and creating the main app
        from core.app_factory import create_app
        
        logger.info("🏗️ Creating main app...")
        app = create_app(mode="simple")  # Use simple mode to avoid complexity
        
        # Check if app was created
        results['app_created'] = app is not None
        results['app_type'] = type(app).__name__
        
        # Check pages data in Dash
        if hasattr(app, '_pages_data'):
            pages_data = app._pages_data
            results['registered_dash_pages'] = list(pages_data.keys())
            results['dash_pages_count'] = len(pages_data)
            
            logger.info(f"📋 Dash registered pages ({len(pages_data)}):")
            for path, page_info in pages_data.items():
                logger.info(f"  🔗 {path} -> {page_info.get('name', 'Unknown')}")
        else:
            results['dash_pages_data'] = "No _pages_data attribute"
            logger.warning("⚠️ No _pages_data found in app")
        
        # Check app layout
        if hasattr(app, 'layout'):
            layout = app.layout
            results['has_layout'] = layout is not None
            results['layout_type'] = type(layout).__name__ if layout else None
            
            # Check if page_container is in layout
            layout_str = str(layout) if layout else ""
            results['has_page_container'] = '_pages_content' in layout_str or 'page_container' in layout_str
            
            logger.info(f"📐 Layout: {results['layout_type']}, has page_container: {results['has_page_container']}")
        else:
            results['layout_check'] = "No layout attribute"
            logger.warning("⚠️ App has no layout")
            
    except Exception as e:
        results['app_creation_error'] = str(e)
        logger.error(f"❌ App creation failed: {e}")
        
    return results

def diagnose_unicode_handling() -> Dict[str, Any]:
    """Check for Unicode handling issues that might affect rendering."""
    results = {}
    
    try:
        from core.unicode import safe_decode_bytes, safe_encode_text
        
        # Test basic Unicode handling
        test_text = "Test 🔍 Unicode 📊 Content"
        encoded = safe_encode_text(test_text)
        results['unicode_encoding'] = 'SUCCESS'
        
        test_bytes = test_text.encode('utf-8')
        decoded = safe_decode_bytes(test_bytes)
        results['unicode_decoding'] = 'SUCCESS'
        
        logger.info("✅ Unicode handling works")
        
    except Exception as e:
        results['unicode_error'] = str(e)
        logger.error(f"❌ Unicode handling failed: {e}")
        
    return results

def run_full_diagnosis():
    """Run complete diagnosis of the project's Dash setup."""
    print("🔍 Starting comprehensive Dash Pages diagnosis...\n")
    
    # Test 1: Page Registry
    print("1️⃣ Testing page registry system...")
    registry_results = diagnose_page_registry()
    
    # Test 2: Main App Creation  
    print("\n2️⃣ Testing main app creation...")
    app_results = diagnose_dash_app()
    
    # Test 3: Unicode Handling
    print("\n3️⃣ Testing Unicode handling...")
    unicode_results = diagnose_unicode_handling()
    
    # Summary Report
    print("\n" + "="*60)
    print("📋 DIAGNOSIS SUMMARY")
    print("="*60)
    
    # Page Registry Summary
    if 'working_pages' in registry_results:
        working = registry_results['working_pages']
        total = registry_results['total_pages']
        print(f"📄 Page Registry: {working}/{total} pages working")
    else:
        print(f"📄 Page Registry: FAILED - {registry_results.get('page_registry_error', 'Unknown error')}")
    
    # App Creation Summary
    if app_results.get('app_created'):
        dash_pages = app_results.get('dash_pages_count', 0)
        has_container = app_results.get('has_page_container', False)
        print(f"🏗️ App Creation: SUCCESS")
        print(f"   📋 Dash pages registered: {dash_pages}")
        print(f"   📐 Has page_container: {has_container}")
    else:
        print(f"🏗️ App Creation: FAILED - {app_results.get('app_creation_error', 'Unknown error')}")
    
    # Unicode Summary
    if unicode_results.get('unicode_encoding') == 'SUCCESS':
        print(f"🔤 Unicode Handling: SUCCESS")
    else:
        print(f"🔤 Unicode Handling: FAILED - {unicode_results.get('unicode_error', 'Unknown error')}")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if registry_results.get('working_pages', 0) < registry_results.get('total_pages', 0):
        print("   🔧 Fix individual page imports first")
        
    if not app_results.get('app_created'):
        print("   🔧 Fix app creation issues before testing pages")
        
    if app_results.get('dash_pages_count', 0) == 0:
        print("   🔧 No pages registered with Dash - registration system not working")
        
    if not app_results.get('has_page_container'):
        print("   🔧 page_container missing from layout - pages won't render")
        
    if app_results.get('app_created') and app_results.get('has_page_container') and app_results.get('dash_pages_count', 0) > 0:
        print("   ✅ Core setup looks good - issue may be in page content or navigation")
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Run individual_page_test.py to test page layouts")
    print("   2. Run minimal_dash_pages_test.py to test basic Dash Pages")
    print("   3. If both work, issue is in main app integration")
    
    return {
        'registry': registry_results,
        'app': app_results, 
        'unicode': unicode_results
    }

if __name__ == '__main__':
    run_full_diagnosis()
