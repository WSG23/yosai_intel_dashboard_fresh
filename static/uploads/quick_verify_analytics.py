# quick_verify_analytics.py - FIXED: Quick verification script
"""
Quick verification script for analytics components
Run this to immediately check if everything is working
"""

import sys
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

def test_imports():
    """Test if all components can be imported"""
    logger.info("🔍 Testing imports...")
    
    try:
        from components.analytics import (
            FileProcessor,
            AnalyticsGenerator,
            create_dual_file_uploader,
            create_data_preview
        )
        logger.info("✅ All imports successful")
        return True
    except ImportError as e:
        logger.info(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality with minimal data"""
    logger.info("\n🧪 Testing basic functionality...")
    
    try:
        from components.analytics import FileProcessor, AnalyticsGenerator
        
        # Create minimal test data
        test_df = pd.DataFrame({
            'user': ['A', 'B'],
            'door': ['X', 'Y'],
            'result': ['OK', 'DENIED']
        })
        
        # Test validation
        valid, msg, suggestions = FileProcessor.validate_dataframe(test_df)
        if valid:
            logger.info("✅ Data validation works")
        else:
            logger.info(f"❌ Data validation failed: {msg}")
            return False
        
        # Test analytics generation
        analytics = AnalyticsGenerator.generate_analytics(test_df)
        if analytics and analytics.get('total_events') == 2:
            logger.info("✅ Analytics generation works")
        else:
            logger.info("❌ Analytics generation failed")
            return False
        
        return True
        
    except Exception as e:
        logger.info(f"❌ Basic functionality test failed: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid inputs"""
    logger.info("\n🛡️ Testing error handling...")
    
    try:
        from components.analytics import FileProcessor, AnalyticsGenerator
        
        # Test with invalid file content
        result = FileProcessor.process_file_content("invalid", "test.csv")
        if result is None:
            logger.info("✅ Invalid content handling works")
        else:
            logger.info("❌ Invalid content handling failed")
            return False
        
        # Test with empty DataFrame
        empty_analytics = AnalyticsGenerator.generate_analytics(pd.DataFrame())
        if empty_analytics == {}:
            logger.info("✅ Empty data handling works")
        else:
            logger.info("❌ Empty data handling failed")
            return False
        
        return True
        
    except Exception as e:
        logger.info(f"❌ Error handling test failed: {e}")
        return False

def test_component_creation():
    """Test if UI components can be created"""
    logger.info("\n🎨 Testing component creation...")
    
    try:
        from components.analytics import create_dual_file_uploader, create_data_preview
        
        # Test file uploader
        uploader = create_dual_file_uploader()
        if uploader is not None:
            logger.info("✅ File uploader creation works")
        else:
            logger.info("❌ File uploader creation failed")
            return False
        
        # Test data preview with sample data
        sample_df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        preview = create_data_preview(sample_df, "test.csv")
        if preview is not None:
            logger.info("✅ Data preview creation works")
        else:
            logger.info("❌ Data preview creation failed")
            return False
        
        return True
        
    except Exception as e:
        logger.info(f"❌ Component creation test failed: {e}")
        return False

def main():
    """Run quick verification"""
    logger.info("⚡ QUICK ANALYTICS VERIFICATION")
    logger.info("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Error Handling", test_error_handling),
        ("Component Creation", test_component_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
        else:
            logger.info(f"   💥 {test_name} failed!")
    
    logger.info("\n" + "=" * 40)
    logger.info(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("\n✅ Your analytics components are ready!")
        logger.info("Next: Run your app and navigate to /analytics")
    else:
        logger.info("⚠️  Some tests failed")
        logger.info("\n🔧 Fixes needed:")
        if passed < 1:
            logger.info("- Check if components/analytics/ directory exists")
            logger.info("- Verify __init__.py files are present")
            logger.info("- Install required packages: pandas, plotly, dash-bootstrap-components")
        else:
            logger.info("- Review the error messages above")
            logger.info("- Check individual component files")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)