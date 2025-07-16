#!/usr/bin/env python3
"""
DEEP ANALYTICS SPECIFIC DEBUG SCRIPT
Tests the exact code path that the deep analytics page uses
"""

import logging
import sys

import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_deep_analytics_specific_path():
    """Test the exact code path that deep analytics page uses"""

    print("🎯 DEEP ANALYTICS SPECIFIC DEBUG")
    print("=" * 60)

    # Step 1: Setup test data (same as diagnostic)
    print("📊 STEP 1: Setting up test data")
    test_data = []
    for i in range(2500):
        test_data.append(
            {
                "person_id": f"USER_{i % 200}",
                "door_id": f"DOOR_{i % 100}",
                "access_result": "Granted" if i % 3 != 0 else "Denied",
                "timestamp": f"2024-01-{(i % 30) + 1:02d} {(i % 24):02d}:{(i % 60):02d}:00",
            }
        )

    original_df = pd.DataFrame(test_data)

    # Add to upload store
    try:
        from utils.upload_store import uploaded_data_store

        uploaded_data_store.clear_all()
        uploaded_data_store.add_file("test_deep_analytics.csv", original_df)
        print(f"✅ Added {len(original_df):,} rows to upload store")
    except Exception as e:
        print(f"❌ Error setting up upload store: {e}")
        return
    print()

    # Step 2: Test deep analytics get_analytics_service_safe
    print("🔧 STEP 2: Testing get_analytics_service_safe")
    try:
        from pages.deep_analytics_complex.analysis import get_analytics_service_safe

        service = get_analytics_service_safe()
        if service:
            print("✅ Deep analytics service available")
        else:
            print("❌ Deep analytics service not available")
            return
    except Exception as e:
        print(f"❌ Error getting deep analytics service: {e}")
        return
    print()

    # Step 3: Test the exact method deep analytics calls
    print("⚙️  STEP 3: Testing service.get_analytics_by_source('uploaded')")
    try:
        result = service.get_analytics_by_source("uploaded")

        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Total events: {result.get('total_events', 'N/A'):,}")
        print(f"   Message: {result.get('message', 'none')}")

        # CHECK FOR 150!
        if result.get("total_events") == 150:
            print("   🚨 FOUND THE 150 ROW LIMIT HERE!")
            print("   This is why deep analytics shows 150!")
        elif result.get("total_events") == 2500:
            print("   ✅ Service correctly returns 2,500 rows")
        else:
            print(f"   ⚠️  Unexpected row count: {result.get('total_events')}")

    except Exception as e:
        print(f"❌ Error testing get_analytics_by_source: {e}")
        import traceback

        traceback.print_exc()
    print()

    # Step 4: Test analyze_data_with_service_safe directly
    print(
        "🎯 STEP 4: Testing analyze_data_with_service_safe (the exact deep analytics function)"
    )
    try:
        from pages.deep_analytics_complex.analysis import analyze_data_with_service_safe

        # Test with different data sources
        test_sources = [
            "uploaded",
            "service:uploaded",
            "upload:test_deep_analytics.csv",
        ]

        for source in test_sources:
            print(f"   Testing source: '{source}'")

            result = analyze_data_with_service_safe(source, "security")

            if isinstance(result, dict) and "error" in result:
                print(f"     ❌ Error: {result['error']}")
            else:
                total_events = result.get("total_events", 0)
                print(f"     📊 Total events: {total_events:,}")

                # CHECK FOR 150!
                if total_events == 150:
                    print("     🚨 FOUND THE 150 ROW LIMIT HERE!")
                    print("     This function is returning 150 to deep analytics!")
                elif total_events == 2500:
                    print("     ✅ Function correctly returns 2,500 rows")
                else:
                    print(f"     ⚠️  Unexpected count: {total_events}")
            print()

    except Exception as e:
        print(f"❌ Error testing analyze_data_with_service_safe: {e}")
        import traceback

        traceback.print_exc()
    print()

    # Step 5: Test sample data generation (common source of 150)
    print("🔬 STEP 5: Testing sample data generation")
    try:
        from services.analytics_summary import (
            create_sample_data,
            generate_sample_analytics,
        )

        # Test create_sample_data
        sample_df = create_sample_data()
        print(f"   create_sample_data(): {len(sample_df):,} rows")

        if len(sample_df) == 150:
            print("   🚨 FOUND 150 ROW LIMIT in create_sample_data()!")

        # Test generate_sample_analytics
        sample_result = generate_sample_analytics()
        total_events = sample_result.get("total_events", 0)
        print(f"   generate_sample_analytics(): {total_events:,} total events")

        if total_events == 150:
            print("   🚨 FOUND 150 ROW LIMIT in generate_sample_analytics()!")
            print("   Deep analytics is falling back to sample data!")

    except Exception as e:
        print(f"❌ Error testing sample data: {e}")
    print()

    # Step 6: Test data source options
    print("📋 STEP 6: Testing get_data_source_options_safe")
    try:
        from pages.deep_analytics_complex.analysis import get_data_source_options_safe

        options = get_data_source_options_safe()
        print(f"   Available data sources:")

        for option in options:
            print(f"     {option['label']} -> {option['value']}")

        # Check if uploaded data is detected
        upload_options = [
            opt
            for opt in options
            if "upload:" in opt["value"] or opt["value"] == "uploaded"
        ]
        if upload_options:
            print(f"   ✅ Uploaded data detected: {len(upload_options)} options")
        else:
            print(f"   ❌ No uploaded data options found - this could be the issue!")

    except Exception as e:
        print(f"❌ Error testing data source options: {e}")
    print()

    # Step 7: Test file upload detection
    print("📁 STEP 7: Testing file upload detection")
    try:
        from services.upload_data_service import get_uploaded_data

        uploaded_files = get_uploaded_data()

        if uploaded_files:
            print(f"   ✅ Found {len(uploaded_files)} uploaded files:")
            for filename, df in uploaded_files.items():
                print(f"     {filename}: {len(df):,} rows")
        else:
            print(f"   ❌ No uploaded files detected!")
            print(f"   This means deep analytics can't find your data!")

    except Exception as e:
        print(f"❌ Error testing file upload detection: {e}")
    print()

    # Step 8: Trace the complete deep analytics flow
    print("🔍 STEP 8: Tracing complete deep analytics flow")
    try:
        print("   Simulating deep analytics button click:")

        # 1. Get data source options
        from pages.deep_analytics_complex.analysis import get_data_source_options_safe

        options = get_data_source_options_safe()

        # 2. Find uploaded data source
        uploaded_option = None
        for opt in options:
            if "upload:" in opt["value"] or opt["value"] == "uploaded":
                uploaded_option = opt
                break

        if uploaded_option:
            print(f"   📁 Using data source: {uploaded_option['value']}")

            # 3. Call analyze_data_with_service_safe
            from pages.deep_analytics_complex.analysis import (
                analyze_data_with_service_safe,
            )

            result = analyze_data_with_service_safe(
                uploaded_option["value"], "security"
            )

            total_events = result.get("total_events", 0)
            print(f"   📊 Final result: {total_events:,} total events")

            if total_events == 150:
                print("   🚨 CONFIRMED: Deep analytics flow returns 150!")
                print("   This is exactly what the user sees!")
            elif total_events == 2500:
                print("   ✅ Deep analytics flow works correctly!")
            else:
                print(f"   ⚠️  Unexpected result: {total_events}")

        else:
            print("   ❌ No uploaded data source found in options!")
            print("   Deep analytics will fall back to sample data (150 rows)")

    except Exception as e:
        print(f"❌ Error tracing deep analytics flow: {e}")
        import traceback

        traceback.print_exc()
    print()

    # Final summary
    print("🎯 DEBUG SUMMARY")
    print("=" * 60)
    print("Look for '🚨 FOUND THE 150 ROW LIMIT' messages above.")
    print("This will show you exactly where deep analytics gets 150 instead of 2,500.")
    print("\nMost likely causes:")
    print("1. Deep analytics can't find uploaded data (falls back to sample)")
    print("2. Sample data generation creates exactly 150 rows")
    print("3. get_analytics_by_source() method has issues")
    print("4. Data source detection in deep analytics page is broken")


if __name__ == "__main__":
    test_deep_analytics_specific_path()
