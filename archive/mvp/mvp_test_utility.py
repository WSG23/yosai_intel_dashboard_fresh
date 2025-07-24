#!/usr/bin/env python3
"""
Modular Testing Utility for MVP
Isolate and test individual components without full system
"""

import json
import logging
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from analytics_core.callbacks.unified_callback_manager import CallbackManager
from core.unicode import UnicodeProcessor
from services.data_processing.analytics_engine import AnalyticsEngine
from services.data_processing.data_enhancer import (
    clean_unicode_text,
    sanitize_dataframe,
)
from services.data_processing.processor import Processor

# Import your existing services
from services.data_processing.unified_upload_validator import UnifiedUploadValidator

logger = logging.getLogger(__name__)


class ComponentTester:
    """Utility to test individual components in isolation"""

    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_results = {}

    def create_test_data(self, rows: int = 100) -> pd.DataFrame:
        """Create sample test data with potential Unicode issues"""
        data = {
            "id": range(1, rows + 1),
            "name": [f"User {i}" for i in range(1, rows + 1)],
            "device": [f"Device_{i%10}" for i in range(1, rows + 1)],
            "access_result": [
                "Granted" if i % 3 != 0 else "Denied" for i in range(1, rows + 1)
            ],
            "timestamp": pd.date_range("2024-01-01", periods=rows, freq="H"),
            # Add problematic Unicode data
            "notes": [
                (
                    f"Test note {i} with unicode: café résumé naïve"
                    if i % 5 == 0
                    else f"Regular note {i}"
                )
                for i in range(1, rows + 1)
            ],
        }
        return pd.DataFrame(data)

    def save_test_file(self, df: pd.DataFrame, filename: str = "test_data.csv") -> str:
        """Save test data to file"""
        filepath = self.temp_dir / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        return str(filepath)

    def test_validator(self, filepath: str) -> Dict[str, Any]:
        """Test UnifiedUploadValidator in isolation"""
        logger.info("\n🔍 Testing File Validator...")

        try:
            validator = UnifiedUploadValidator()
            result = validator.validate_file(filepath)

            logger.info("  ✓ Validation result: %s", result.get("valid", False))
            if not result.get("valid", False):
                logger.error(
                    "  ❌ Validation error: %s", result.get("error", "Unknown")
                )

            return {"component": "validator", "success": True, "result": result}

        except Exception as e:
            logger.error("  ❌ Validator test failed: %s", e)
            return {"component": "validator", "success": False, "error": str(e)}

    def test_unicode_processor(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test Unicode processing in isolation"""
        logger.info("\n🔤 Testing Unicode Processor...")

        try:
            # Test DataFrame sanitization
            original_rows = len(df)
            sanitized_df = sanitize_dataframe(df)

            logger.info("  ✓ Sanitized %s rows", original_rows)
            logger.info(
                "  ✓ Result: %s rows, %s columns",
                len(sanitized_df),
                len(sanitized_df.columns),
            )

            # Test text cleaning
            test_text = "Test with surrogates: \ud83d\ude00 and café"
            cleaned_text = clean_unicode_text(test_text)
            logger.info("  ✓ Text cleaning: '%s' -> '%s'", test_text, cleaned_text)

            return {
                "component": "unicode_processor",
                "success": True,
                "original_rows": original_rows,
                "sanitized_rows": len(sanitized_df),
                "text_cleaned": cleaned_text,
            }

        except Exception as e:
            logger.error("  ❌ Unicode processor test failed: %s", e)
            return {"component": "unicode_processor", "success": False, "error": str(e)}

    def test_data_enhancer(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test data enhancement in isolation"""
        logger.info("\n⚡ Testing Data Enhancer...")

        try:
            processor = Processor()

            # First sanitize
            clean_df = sanitize_dataframe(df)

            # Then enhance
            enhanced_df = processor.enhance_dataframe(clean_df)

            logger.info("  ✓ Enhanced %s -> %s rows", len(clean_df), len(enhanced_df))
            logger.info(
                "  ✓ Columns: %s -> %s", len(clean_df.columns), len(enhanced_df.columns)
            )
            logger.info(
                "  ✓ New columns: %s", set(enhanced_df.columns) - set(clean_df.columns)
            )

            return {
                "component": "data_enhancer",
                "success": True,
                "original_rows": len(clean_df),
                "enhanced_rows": len(enhanced_df),
                "original_columns": len(clean_df.columns),
                "enhanced_columns": len(enhanced_df.columns),
                "new_columns": list(set(enhanced_df.columns) - set(clean_df.columns)),
            }

        except Exception as e:
            logger.error("  ❌ Data enhancer test failed: %s", e)
            return {"component": "data_enhancer", "success": False, "error": str(e)}

    def test_analytics_engine(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test analytics generation in isolation"""
        logger.info("\n📊 Testing Analytics Engine...")

        try:
            analytics = AnalyticsEngine()
            result = analytics.generate_analytics(df)

            logger.info("  ✓ Generated analytics with %s metrics", len(result))
            logger.info("  ✓ Analytics keys: %s", list(result.keys()))

            return {
                "component": "analytics_engine",
                "success": True,
                "metrics_count": len(result),
                "metrics": result,
            }

        except Exception as e:
            logger.error("  ❌ Analytics engine test failed: %s", e)
            return {"component": "analytics_engine", "success": False, "error": str(e)}

    def test_callback_manager(self) -> Dict[str, Any]:
        """Test callback system in isolation"""
        logger.info("\n📡 Testing Callback Manager...")

        try:
            callback_manager = CallbackManager()
            events_received = []

            def test_callback(source: str, data: Dict[str, Any]):
                events_received.append({"source": source, "data": data})

            # Register callback
            from core.callback_events import CallbackEvent

            callback_manager.add_callback(
                CallbackEvent.FILE_UPLOAD_COMPLETE, test_callback
            )

            # Trigger event
            callback_manager.trigger(
                CallbackEvent.FILE_UPLOAD_COMPLETE,
                "test_source",
                {"test_data": "test_value"},
            )

            logger.info(
                "  ✓ Callback system working: %s events received", len(events_received)
            )

            return {
                "component": "callback_manager",
                "success": True,
                "events_received": len(events_received),
                "events": events_received,
            }

        except Exception as e:
            logger.error("  ❌ Callback manager test failed: %s", e)
            return {"component": "callback_manager", "success": False, "error": str(e)}

    def run_full_test_suite(self, rows: int = 50) -> Dict[str, Any]:
        """Run complete isolated testing of all components"""
        logger.info("\n🚀 Running Full Component Test Suite (%s rows)", rows)
        logger.info("=" * 60)

        # Create test data
        df = self.create_test_data(rows)
        filepath = self.save_test_file(df)

        results = {
            "test_timestamp": pd.Timestamp.now().isoformat(),
            "test_data_rows": len(df),
            "test_data_columns": len(df.columns),
            "components": {},
        }

        # Test each component in isolation
        test_methods = [
            (self.test_validator, filepath),
            (self.test_unicode_processor, df),
            (self.test_data_enhancer, df),
            (self.test_analytics_engine, df),
            (self.test_callback_manager, None),
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
                logger.error("  ❌ Test method failed: %s", e)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📋 Test Summary:")
        successful = 0
        total = len(results["components"])

        for component, result in results["components"].items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info("  %s %s", status, component)
            if result["success"]:
                successful += 1

        logger.info("\n📊 Overall: %s/%s components passed", successful, total)
        results["summary"] = {
            "passed": successful,
            "total": total,
            "success_rate": successful / total,
        }

        return results

    def save_test_results(
        self, results: Dict[str, Any], filename: str = "test_results.json"
    ):
        """Save test results to file"""
        output_file = self.temp_dir / filename
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info("\n💾 Test results saved to: %s", output_file)
        return str(output_file)

    def cleanup(self):
        """Clean up temporary files"""
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
            logger.info("🧹 Cleaned up temporary directory: %s", self.temp_dir)
        except:
            pass


def main():
    """Main function for command-line usage"""
    import argparse

    parser = argparse.ArgumentParser(description="MVP Component Testing Utility")
    parser.add_argument(
        "--rows", type=int, default=50, help="Number of test rows to generate"
    )
    parser.add_argument(
        "--component",
        choices=["validator", "unicode", "enhancer", "analytics", "callbacks"],
        help="Test specific component only",
    )
    parser.add_argument(
        "--save-results", action="store_true", help="Save test results to file"
    )

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

            logger.info("\n📋 Component Test Result:")
            logger.info(json.dumps(result, indent=2, default=str))

        else:
            # Run full test suite
            results = tester.run_full_test_suite(args.rows)

            if args.save_results:
                tester.save_test_results(results)

            # Exit with error code if tests failed
            success_rate = results["summary"]["success_rate"]
            if success_rate < 1.0:
                logger.warning(
                    "\n⚠️  Some tests failed (success rate: %.1f%%)", success_rate * 100
                )
                sys.exit(1)
            else:
                logger.info("\n🎉 All tests passed!")

    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
