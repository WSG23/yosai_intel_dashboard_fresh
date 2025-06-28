# quick_verify_analytics.py - FIXED: Quick verification script
"""
Quick verification script for analytics components
Run this to immediately check if everything is working
"""

import sys
import pandas as pd
from datetime import datetime

def test_imports():
    """Test if all components can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from components.analytics import (
            FileProcessor,
            AnalyticsGenerator,
            create_dual_file_uploader,
            create_data_preview
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality with minimal data"""
    print("\n🧪 Testing basic functionality...")
    
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
            print("✅ Data validation works")
        else:
            print(f"❌ Data validation failed: {msg}")
            return False
        
        # Test analytics generation
        analytics = AnalyticsGenerator.generate_analytics(test_df)
        if analytics and analytics.get('total_events') == 2:
            print("✅ Analytics generation works")
        else:
            print("❌ Analytics generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\n🛡️ Testing error handling...")
    
    try:
        from components.analytics import FileProcessor, AnalyticsGenerator
        
        # Test with invalid file content
        result = FileProcessor.process_file_content("invalid", "test.csv")
        if result is None:
            print("✅ Invalid content handling works")
        else:
            print("❌ Invalid content handling failed")
            return False
        
        # Test with empty DataFrame
        empty_analytics = AnalyticsGenerator.generate_analytics(pd.DataFrame())
        if empty_analytics == {}:
            print("✅ Empty data handling works")
        else:
            print("❌ Empty data handling failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_component_creation():
    """Test if UI components can be created"""
    print("\n🎨 Testing component creation...")
    
    try:
        from components.analytics import create_dual_file_uploader, create_data_preview
        
        # Test file uploader
        uploader = create_dual_file_uploader()
        if uploader is not None:
            print("✅ File uploader creation works")
        else:
            print("❌ File uploader creation failed")
            return False
        
        # Test data preview with sample data
        sample_df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})
        preview = create_data_preview(sample_df, "test.csv")
        if preview is not None:
            print("✅ Data preview creation works")
        else:
            print("❌ Data preview creation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Component creation test failed: {e}")
        return False

def main():
    """Run quick verification"""
    print("⚡ QUICK ANALYTICS VERIFICATION")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Error Handling", test_error_handling),
        ("Component Creation", test_component_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"   💥 {test_name} failed!")
    
    print("\n" + "=" * 40)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Your analytics components are ready!")
        print("Next: Run your app and navigate to /analytics")
    else:
        print("⚠️  Some tests failed")
        print("\n🔧 Fixes needed:")
        if passed < 1:
            print("- Check if components/analytics/ directory exists")
            print("- Verify __init__.py files are present")
            print("- Install required packages: pandas, plotly, dash-bootstrap-components")
        else:
            print("- Review the error messages above")
            print("- Check individual component files")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)