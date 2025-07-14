#!/usr/bin/env python3
"""
Modular Testing Utility for MVP
Isolate and test individual components without full system
"""

import unittest
import tempfile
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import json
import sys

# Import your existing services
from services.data_processing.unified_upload_validator import UnifiedUploadValidator
from services.data_processing.data_enhancer import sanitize_dataframe, clean_unicode_text
from services.data_processing.processor import Processor
from services.data_processing.analytics_engine import AnalyticsEngine
from core.unicode import UnicodeProcessor
from core.callback_manager import CallbackManager


class ComponentTester:
    """Utility to test individual components in isolation"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_results = {}
        
    def create_test_data(self, rows: int = 100) -> pd.DataFrame:
        """Create sample test data with potential Unicode issues"""
        data = {
            'id': range(1, rows + 1),
            'name': [f'User {i}' for i in range(1, rows + 1)],
            'device': [f'Device_{i%10}' for i in range(1, rows + 1)],
            'access_result': ['Granted' if i % 3 != 0 else 'Denied' for i in range(1, rows + 1)],
            'timestamp': pd.date_range('2024-01-01', periods=rows, freq='H'),
            # Add problematic Unicode data
            'notes': [f'Test note {i} with unicode: café résumé naïve' if i % 5 == 0 
                     else f'Regular note {i}' for i in range(1, rows + 1)]
        }
        return pd.DataFrame(data)
        
    def save_test_file(self, df: pd.DataFrame, filename: str = "test_data.csv") -> str:
        """Save test data to file"""
        filepath = self.temp_dir / filename
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        return str(filepath)
        
    def test_validator(self, filepath: str) -> Dict[str, Any]:
        """Test UnifiedUploadValidator in isolation"""
        print("\n🔍 Testing File Validator...")
        
        try:
            validator = UnifiedUploadValidator()
            result = validator.validate_file(filepath)
            
            print(f"  ✓ Validation result: {result.get('valid', False)}")
            if not result.get('valid', False):
                print(f"  ❌ Validation error: {result.get('error', 'Unknown')}")
                
            return {"component": "validator", "success": True, "result": result}
            
        except Exception as e:
            print(f"  ❌ Validator test failed: {e}")
            return {"component": "validator", "success": False, "error": str(e)}
            
    def test_unicode_processor(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test Unicode processing in isolation"""
        print("\n🔤 Testing Unicode Processor...")
        
        try:
            # Test DataFrame sanitization
            original_rows = len(df)
            sanitized_df = sanitize_dataframe(df)
            
            print(f"  ✓ Sanitized {original_rows} rows")
            print(f"  ✓ Result: {len(sanitized_df)} rows, {len(sanitized_df.columns)} columns")
            
            # Test text cleaning
            test_text = "Test with surrogates: \ud83d\ude00 and café"
            cleaned_text = clean_unicode_text(test_text)
            print(f"  ✓ Text cleaning: '{test_text}' -> '{cleaned_text}'")
            
            return {
                "component": "unicode_processor", 
                "success": True, 
                "original_rows": original_rows,
                "sanitized_rows": len(sanitized_df),
                "text_cleaned": cleaned_text
            }
            
        except Exception as e:
            print(f"  ❌ Unicode processor test failed: {e}")
            return {"component": "unicode_processor", "success": False, "error": str(e)}
            
    def test_data_enhancer(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test data enhancement in isolation"""
        print("\n⚡ Testing Data Enhancer...")
        
        try:
            processor = Processor()
            
            # First sanitize
            clean_df = sanitize_dataframe(df)
            
            # Then enhance
            enhanced_df = processor.enhance_dataframe(clean_df)
            
            print(f"  ✓ Enhanced {len(clean_df)} -> {len(enhanced_df)} rows")
            print(f"  ✓ Columns: {len(clean_df.columns)} -> {len(enhanced_df.columns)}")
            print(f"  ✓ New columns: {set(enhanced_df.columns) - set(clean_df.columns)}")
            
            return {
                "component": "data_enhancer",
                "success": True,
                "original_rows": len(clean_df),
                "enhanced_rows": len(enhanced_df),
                "original_columns": len(clean_df.columns),
                "enhanced_columns": len(enhanced_df.columns),
                "new_columns": list(set(enhanced_df.columns) - set(clean_df.columns))
            }
            
        except Exception as e:
            print(f"  ❌ Data enhancer test failed: {e}")
            return {"component": "data_enhancer", "success": False, "error": str(e)}
            
    def test_analytics_engine(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test analytics generation in isolation"""
        print("\n📊 Testing Analytics Engine...")
        
        try:
            analytics = AnalyticsEngine()
            result = analytics.generate_analytics(df)
            
            print(f"  ✓ Generated analytics with {len(result)} metrics")
            print(f"  ✓ Analytics keys: {list(result.keys())}")
            
            return {
                "component": "analytics_engine",
                "success": True,
                "metrics_count": len(result),
                "metrics": result
            }
            
        except Exception as e:
            print(f"  ❌ Analytics engine test failed: {e}")
            return {"component": "analytics_engine", "success": False, "error": str(e)}
            
    def test_callback_manager(self) -> Dict[str, Any]:
        """Test callback system in isolation"""
        print("\n📡 Testing Callback Manager...")
        
        try:
            callback_manager = CallbackManager()
            events_received = []
            
            def test_callback(source: str, data: Dict[str, Any]):
                events_received.append({"source": source, "data": data})
                
            # Register callback
            from core.callback_events import CallbackEvent
            callback_manager.add_callback(CallbackEvent.FILE_UPLOAD_COMPLETE, test_callback)
            
            # Trigger event
            callback_manager.trigger(
                CallbackEvent.FILE_UPLOAD_COMPLETE, 
                "test_source", 
                {"test_data": "test_value"}
            )
            
            print(f"  ✓ Callback system working: {len(events_received)} events received")
            
            return {
                "component": "callback_manager",
                "success": True,
                "events_received": len(events_received),
                "events": events_received
            }
            
        except Exception as e:
            print(f"  ❌ Callback manager test failed: {e}")
            return {"component": "callback_manager", "success": False, "error": str(e)}
            
    def run_full_test_suite(self, rows: int = 50) -> Dict[str, Any]:
        """Run complete isolated testing of all components"""
        print(f"\n🚀 Running Full Component Test Suite ({rows} rows)")
        print("=" * 60)
        
        # Create test data
        df = self.create_test_data(rows)
        filepath = self.save_test_file(df)
        
        results = {
            "test_timestamp": pd.Timestamp.now().isoformat(),
            "test_data_rows": len(df),
            "test_data_columns": len(df.columns),
            "components": {}
        }
        
        # Test each component in isolation
        test_methods = [
            (self.test_validator, filepath),
            (self.test_unicode_processor, df),
            (self.test_data_enhancer, df),
            (self.test_analytics_engine, df),
            (self.test_callback_manager, None)
        ]
        
        for test_method, arg in test_methods:
            try:
                if arg is not None:
                    result = test_method(arg)
                else:
                    result = test_method()
                    
                component_name = result["component"]
                results["components"][component_name] = result
                
            except Exception as e:
                print(f"  ❌ Test method failed: {e}")
                
        # Summary
        print("\n" + "=" * 60)
        print("📋 Test Summary:")
        successful = 0
        total = len(results["components"])
        
        for component, result in results["components"].items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"  {status} {component}")
            if result["success"]:
                successful += 1
                
        print(f"\n📊 Overall: {successful}/{total} components passed")
        results["summary"] = {"passed": successful, "total": total, "success_rate": successful/total}
        
        return results
        
    def save_test_results(self, results: Dict[str, Any], filename: str = "test_results.json"):
        """Save test results to file"""
        output_file = self.temp_dir / filename
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Test results saved to: {output_file}")
        return str(output_file)
        
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up temporary directory: {self.temp_dir}")
        except:
            pass


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MVP Component Testing Utility")
    parser.add_argument("--rows", type=int, default=50, help="Number of test rows to generate")
    parser.add_argument("--component", choices=["validator", "unicode", "enhancer", "analytics", "callbacks"], 
                       help="Test specific component only")
    parser.add_argument("--save-results", action="store_true", help="Save test results to file")
    
    args = parser.parse_args()
    
    tester = ComponentTester()
    
    try:
        if args.component:
            # Test specific component
            df = tester.create_test_data(args.rows)
            filepath = tester.save_test_file(df)
            
            if args.component == "validator":
                result = tester.test_validator(filepath)
            elif args.component == "unicode":
                result = tester.test_unicode_processor(df)
            elif args.component == "enhancer":
                result = tester.test_data_enhancer(df)
            elif args.component == "analytics":
                result = tester.test_analytics_engine(df)
            elif args.component == "callbacks":
                result = tester.test_callback_manager()
                
            print(f"\n📋 Component Test Result:")
            print(json.dumps(result, indent=2, default=str))
            
        else:
            # Run full test suite
            results = tester.run_full_test_suite(args.rows)
            
            if args.save_results:
                tester.save_test_results(results)
                
            # Exit with error code if tests failed
            success_rate = results["summary"]["success_rate"]
            if success_rate < 1.0:
                print(f"\n⚠️  Some tests failed (success rate: {success_rate:.1%})")
                sys.exit(1)
            else:
                print(f"\n🎉 All tests passed!")
                
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()