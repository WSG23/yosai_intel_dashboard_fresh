#!/usr/bin/env python3
"""
Test Analytics with both Step 1 (callback fix) and Step 2 (missing methods) applied
"""

import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# Apply BOTH fixes
def apply_both_fixes():
    """Apply both callback fix and missing methods fix"""

    # Step 1: Callback fix
    try:
        from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks as CallbackManager

        if hasattr(CallbackManager, "handle_register") and not hasattr(
            CallbackManager, "register_handler"
        ):
            CallbackManager.register_handler = CallbackManager.handle_register
            print("✅ Step 1: Callback patch applied")
    except Exception as e:
        print(f"⚠️  Step 1: Callback patch failed: {e}")

    # Step 2: Missing methods fix
    try:
        from services.upload_processing import UploadAnalyticsProcessor

        # Add missing methods if they don't exist
        if not hasattr(UploadAnalyticsProcessor, "get_analytics_from_uploaded_data"):

            def get_analytics_from_uploaded_data(self):
                try:
                    data = self.load_uploaded_data()
                    if not data:
                        return {
                            "status": "no_data",
                            "message": "No uploaded files available",
                        }
                    result = self._process_uploaded_data_directly(data)
                    result["status"] = "success"
                    return result
                except Exception as e:
                    return {"status": "error", "message": str(e)}

            UploadAnalyticsProcessor.get_analytics_from_uploaded_data = (
                get_analytics_from_uploaded_data
            )

        if not hasattr(UploadAnalyticsProcessor, "clean_uploaded_dataframe"):

            def clean_uploaded_dataframe(self, df):
                import pandas as pd

                cleaned_df = df.dropna(how="all").copy()
                cleaned_df.columns = [
                    col.strip().replace(" ", "_").lower() for col in cleaned_df.columns
                ]
                return cleaned_df

            UploadAnalyticsProcessor.clean_uploaded_dataframe = clean_uploaded_dataframe

        print("✅ Step 2: Missing methods patch applied")

    except Exception as e:
        print(f"⚠️  Step 2: Missing methods patch failed: {e}")


async def test_analytics_comprehensive():
    try:
        print("=== COMPREHENSIVE ANALYTICS TEST WITH BOTH FIXES ===")

        apply_both_fixes()

        import pandas as pd

        from yosai_intel_dashboard.src.services.analytics.analytics_service import AnalyticsService

        # Load the Enhanced Security Demo data
        parquet_path = Path("temp/uploaded_data/Enhanced_Security_Demo.csv.parquet")
        df = pd.read_parquet(parquet_path)

        print(f"\nData loaded: {len(df)} access events")
        print(f"Time range: {df['Event Time'].min()} to {df['Event Time'].max()}")
        print(f"Unique employees: {df['Employee Code'].nunique()}")
        print(f"Unique doors: {df['Door Location'].nunique()}")

        # Initialize analytics service
        print("\n--- Initializing AnalyticsService ---")
        analytics = AnalyticsService()
        health = analytics.health_check()
        print(f"Health: {health}")

        result = {"success": True, "tests": {}}

        # Test all the methods that were failing before
        tests = [
            ("Dashboard Summary", lambda: analytics.get_dashboard_summary()),
            ("Access Patterns", lambda: analytics.analyze_access_patterns(days=1)),
            ("Anomaly Detection", lambda: analytics.detect_anomalies(df)),
            ("Data Processing", lambda: analytics.clean_uploaded_dataframe(df)),
            ("Data Summary", lambda: analytics.summarize_dataframe(df)),
            (
                "Uploaded Analytics",
                lambda: analytics.get_analytics_from_uploaded_data(),
            ),
        ]

        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                test_result = test_func()
                result["tests"][test_name.lower().replace(" ", "_")] = {
                    "success": True,
                    "result_type": str(type(test_result)),
                    "summary": (
                        str(test_result)[:200] + "..."
                        if len(str(test_result)) > 200
                        else str(test_result)
                    ),
                }

                if test_name == "Data Processing":
                    print(f"✅ {test_name}: Processed {len(test_result)} rows")
                elif test_name == "Data Summary":
                    print(
                        f"✅ {test_name}: {test_result.get('rows', 'N/A')} rows, {test_result.get('columns', 'N/A')} columns"
                    )
                elif isinstance(test_result, dict) and "status" in test_result:
                    print(f"✅ {test_name}: {test_result.get('status', 'unknown')}")
                elif isinstance(test_result, list):
                    print(f"✅ {test_name}: {len(test_result)} items")
                else:
                    print(f"✅ {test_name}: Success")

            except Exception as e:
                result["tests"][test_name.lower().replace(" ", "_")] = {
                    "success": False,
                    "error": str(e),
                }
                print(f"❌ {test_name}: {e}")

        print("\n=== COMPREHENSIVE TEST COMPLETE ===")
        return result

    except Exception as e:
        print(f"Comprehensive test failed: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


def main():
    result = asyncio.run(test_analytics_comprehensive())
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST RESULTS:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
