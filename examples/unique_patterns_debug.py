#!/usr/bin/env python3
"""
UNIQUE PATTERNS SPECIFIC DEBUG
Test the exact code path that's causing 150 rows in unique patterns analysis
"""

import logging
import sys

import pandas as pd

logger = logging.getLogger(__name__)


def create_test_dataset(num_rows: int = 2500) -> pd.DataFrame:
    """Return a synthetic dataset used for debugging."""

    test_data = []
    for i in range(num_rows):
        test_data.append(
            {
                "person_id": f"USER_{i % 200}",
                "door_id": f"DOOR_{i % 100}",
                "access_result": "Granted" if i % 3 != 0 else "Denied",
                "timestamp": f"2024-01-{(i % 30) + 1:02d} {(i % 24):02d}:{(i % 60):02d}:00",
            }
        )

    return pd.DataFrame(test_data)


def add_to_upload_store(df: pd.DataFrame) -> None:
    """Store ``df`` in the upload store used by the service."""

    from utils.upload_store import uploaded_data_store

    uploaded_data_store.clear_all()
    uploaded_data_store.add_file("debug_unique_patterns.csv", df)
    print(f"✅ Added {len(df):,} rows to upload store")


def get_uploaded_data() -> dict[str, pd.DataFrame]:
    """Return uploaded files via the service."""

    from services.upload_data_service import get_uploaded_data

    return get_uploaded_data()


def create_service():
    """Instantiate and return ``AnalyticsService``."""

    from services import AnalyticsService

    return AnalyticsService()


def clean_uploaded_dataframe(service, df: pd.DataFrame) -> pd.DataFrame:
    """Return ``df`` after cleaning via ``service``."""

    return service.clean_uploaded_dataframe(df)


def run_unique_patterns_analysis(service) -> dict:
    """Execute ``get_unique_patterns_analysis`` and return the result."""

    return service.get_unique_patterns_analysis()


def manual_unique_patterns_steps() -> None:
    """Replicate the unique pattern logic step by step for debugging."""

    print("   6a. Getting uploaded data...")
    uploaded_data = get_uploaded_data()
    print(f"      Found {len(uploaded_data)} files")

    print("   6b. Processing first file...")
    filename, df = next(iter(uploaded_data.items()))
    print(f"      Original: {len(df):,} rows")

    print("   6c. Cleaning dataframe...")
    from utils.mapping_helpers import map_and_clean

    cleaned_df = map_and_clean(df)
    print(f"      After map_and_clean: {len(cleaned_df):,} rows")

    if len(cleaned_df) == 150:
        print(f"      🚨 FOUND 150 ROW LIMIT in map_and_clean!")

    print("   6d. Calculating statistics...")
    total_records = len(cleaned_df)
    unique_users = (
        cleaned_df["person_id"].nunique() if "person_id" in cleaned_df.columns else 0
    )
    unique_devices = (
        cleaned_df["door_id"].nunique() if "door_id" in cleaned_df.columns else 0
    )

    print("      Final statistics:")
    print(f"        Total records: {total_records:,}")
    print(f"        Unique users: {unique_users:,}")
    print(f"        Unique devices: {unique_devices:,}")

    if total_records == 150:
        print("      🚨 CONFIRMED: The issue is in the data processing pipeline!")


def check_sampling_limits() -> None:
    """Look for common data-limiting calls in the service implementation."""

    import inspect
    from services.analytics_service import AnalyticsService

    source = inspect.getsource(AnalyticsService.clean_uploaded_dataframe)

    if ".head(" in source:
        print("   🚨 FOUND .head() call in clean_uploaded_dataframe!")
    if ".sample(" in source:
        print("   🚨 FOUND .sample() call in clean_uploaded_dataframe!")
    if "nrows" in source:
        print("   🚨 FOUND nrows parameter in clean_uploaded_dataframe!")
    if "150" in source:
        print("   🚨 FOUND hardcoded 150 in clean_uploaded_dataframe!")

    print("   ✅ Source code check complete")


def final_diagnosis() -> None:
    """Display final pointers for investigators."""

    print("🎯 FINAL DIAGNOSIS")
    print("=" * 60)
    print("Key findings:")
    print("1. If you see '🚨 FOUND 150 ROW LIMIT' above, that's the exact location")
    print("2. Most likely locations:")
    print("   - map_and_clean() function")
    print("   - clean_uploaded_dataframe() method")
    print("   - get_unique_patterns_analysis() method")
    print("3. The issue is in data processing, not display")


def test_unique_patterns_specific() -> None:
    """Test the exact unique patterns analysis that's showing 150"""

    print("🎯 UNIQUE PATTERNS ANALYSIS DEBUG")
    print("=" * 60)

    print("📊 STEP 1: Setting up test data")
    original_df = create_test_dataset()

    try:
        add_to_upload_store(original_df)
    except Exception as e:  # pragma: no cover - diagnostic helper
        print(f"❌ Error setting up upload store: {e}")
        return
    print()

    print("📁 STEP 2: Testing get_uploaded_data()")
    try:
        uploaded_data = get_uploaded_data()
        if uploaded_data:
            print(f"   ✅ Found {len(uploaded_data)} files:")
            for filename, df in uploaded_data.items():
                print(f"     {filename}: {len(df):,} rows")
                if len(df) == 150:
                    print("     🚨 FOUND 150 ROW LIMIT in uploaded data!")
        else:
            print("   ❌ No uploaded data found")
            return
    except Exception as e:  # pragma: no cover - diagnostic helper
        print(f"❌ Error testing get_uploaded_data: {e}")
        return
    print()

    print("⚙️  STEP 3: Testing AnalyticsService creation")
    try:
        service = create_service()
        print("   ✅ AnalyticsService created successfully")
    except Exception as e:  # pragma: no cover - diagnostic helper
        print(f"❌ Error creating AnalyticsService: {e}")
        return
    print()

    print("🧹 STEP 4: Testing clean_uploaded_dataframe")
    try:
        filename, df = next(iter(uploaded_data.items()))
        print(f"   Original dataframe: {len(df):,} rows")
        cleaned_df = clean_uploaded_dataframe(service, df)
        print(f"   Cleaned dataframe: {len(cleaned_df):,} rows")
        if len(cleaned_df) == 150:
            print("   🚨 FOUND 150 ROW LIMIT in clean_uploaded_dataframe!")
        elif len(cleaned_df) != len(df):
            print(
                f"   ⚠️  Row count changed during cleaning: {len(df):,} → {len(cleaned_df):,}"
            )
    except Exception as e:  # pragma: no cover - diagnostic helper
        print(f"❌ Error testing clean_uploaded_dataframe: {e}")
        import traceback

        traceback.print_exc()
    print()

    print("🎯 STEP 5: Testing get_unique_patterns_analysis() - THE ACTUAL METHOD")
    try:
        print("   Calling service.get_unique_patterns_analysis()...")
        result = run_unique_patterns_analysis(service)
        print(f"   Status: {result.get('status', 'unknown')}")
        if "data_summary" in result:
            total_records = result["data_summary"].get("total_records", 0)
            print(f"   Total records: {total_records:,}")
            if total_records == 150:
                print("   🚨 FOUND THE 150 ROW LIMIT IN get_unique_patterns_analysis()!")
                print("   This is exactly what shows in the UI!")
            elif total_records == 2500:
                print("   ✅ Method correctly returns 2,500 rows")
            else:
                print(f"   ⚠️  Unexpected count: {total_records}")
            if "unique_entities" in result["data_summary"]:
                users = result["data_summary"]["unique_entities"].get("users", 0)
                devices = result["data_summary"]["unique_entities"].get("devices", 0)
                print(f"   Unique users: {users:,}")
                print(f"   Unique devices: {devices:,}")
        else:
            print("   ❌ No data_summary in result")
            print(f"   Result keys: {list(result.keys())}")
    except Exception as e:  # pragma: no cover - diagnostic helper
        print(f"❌ Error testing get_unique_patterns_analysis: {e}")
        import traceback

        traceback.print_exc()
    print()

    print("🔍 STEP 6: Manual step-by-step test of unique patterns logic")
    try:
        manual_unique_patterns_steps()
    except Exception as e:  # pragma: no cover - diagnostic helper
        print(f"❌ Error in manual testing: {e}")
        import traceback

        traceback.print_exc()
    print()

    print("🔬 STEP 7: Check for data sampling or limiting")
    try:
        print("   Checking for common data limiting patterns...")
        check_sampling_limits()
    except Exception as e:  # pragma: no cover - diagnostic helper
        print(f"❌ Error checking source code: {e}")
    print()

    final_diagnosis()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    test_unique_patterns_specific()
