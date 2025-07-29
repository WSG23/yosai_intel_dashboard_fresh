#!/usr/bin/env python3
"""
COMPLETE DIAGNOSTIC SCRIPT - Find 150 Row Limit
This script traces through the entire data pipeline to find where 150 rows comes from.
"""

import logging
import sys
import traceback
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def create_test_dataset(num_rows: int = 2500) -> pd.DataFrame:
    """Return a simple synthetic dataframe used for the diagnostics."""

    test_data = []
    for i in range(num_rows):
        test_data.append(
            {
                "person_id": f"USER_{i % 200}",  # 200 unique users
                "door_id": f"DOOR_{i % 100}",  # 100 unique doors
                "access_result": "Granted" if i % 3 != 0 else "Denied",
                "timestamp": f"2024-01-{(i % 30) + 1:02d} {(i % 24):02d}:{(i % 60):02d}:00",
            }
        )

    return pd.DataFrame(test_data)


def check_upload_store(df: pd.DataFrame) -> pd.DataFrame | None:
    """Store ``df`` using the global upload store and return the stored copy."""

    from utils.upload_store import uploaded_data_store

    uploaded_data_store.clear_all()
    uploaded_data_store.add_file("test_2500_rows.csv", df)
    stored_data = uploaded_data_store.get_all_data()
    return stored_data.get("test_2500_rows.csv")


def get_uploaded_files() -> dict[str, pd.DataFrame]:
    """Return files available from the upload data service."""

    from services.upload_data_service import get_uploaded_data

    return get_uploaded_data()


def load_service_data() -> dict[str, pd.DataFrame]:
    """Return uploaded data as loaded by ``AnalyticsService``."""

    from services.analytics_service import AnalyticsService

    service = AnalyticsService()
    return service.load_uploaded_data()


def map_and_clean_df(original_df: pd.DataFrame) -> pd.DataFrame:
    """Apply column mapping to ``original_df`` and return the cleaned dataframe."""

    from utils.mapping_helpers import map_and_clean

    test_df_with_ts = original_df.copy()
    test_df_with_ts.columns = [
        "Person ID",
        "Device name",
        "Access result",
        "Timestamp",
    ]
    return map_and_clean(test_df_with_ts)


def summarize_df(df: pd.DataFrame) -> dict:
    """Return a summary dictionary for ``df``."""

    from services.analytics_summary import summarize_dataframe

    return summarize_dataframe(df)


def run_analytics_processing() -> dict:
    """Run the analytics service processing step and return the result."""

    from services.analytics_service import AnalyticsService

    service = AnalyticsService()
    return service._get_real_uploaded_data()


def run_chunked_analytics(df: pd.DataFrame) -> dict:
    """Process ``df`` using the chunked analytics controller."""

    from analytics.chunked_analytics_controller import ChunkedAnalyticsController

    test_df = df.copy()
    test_df.columns = ["person_id", "door_id", "access_result", "timestamp"]
    controller = ChunkedAnalyticsController(chunk_size=10000)
    return controller.process_large_dataframe(test_df, ["security", "behavior"])


def find_hardcoded_values(search_dirs: list[str]) -> list[str]:
    """Return a list of references to the string ``'150'`` in ``search_dirs``."""

    found_150: list[str] = []
    for search_dir in search_dirs:
        if Path(search_dir).exists():
            for py_file in Path(search_dir).rglob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8")
                    if "150" in content:
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if "150" in line and not line.strip().startswith("#"):
                                found_150.append(f"{py_file}:{i+1}: {line.strip()}")
                except Exception:
                    continue
    return found_150


def test_complete_pipeline() -> None:
    """Test the entire data pipeline to find the 150 row limit."""

    print("🔍 COMPLETE PIPELINE DIAGNOSTIC")
    print("=" * 60)

    print("📊 STEP 1: Creating test dataset with 2500 rows")
    original_df = create_test_dataset(2500)
    print(f"✅ Created DataFrame: {len(original_df):,} rows")
    print(f"   Columns: {list(original_df.columns)}")
    print()

    print("📁 STEP 2: Testing upload store")
    try:
        stored_df = check_upload_store(original_df)

        if stored_df is not None:
            print(f"✅ Upload store: {len(stored_df):,} rows stored")
            print(f"   Retrieval successful: {len(stored_df) == len(original_df)}")
        else:
            print("❌ Upload store: Failed to retrieve data")

    except Exception as e:  # pragma: no cover - diagnostic helper
        print(f"❌ Upload store error: {e}")
        traceback.print_exc()
    print()

    print("📤 STEP 3: Testing file upload module")
    try:
        uploaded_files = get_uploaded_files()
        print(f"✅ File upload module found {len(uploaded_files)} files")

        for filename, df in uploaded_files.items():
            print(f"   {filename}: {len(df):,} rows")
            if len(df) == 150:
                print(f"   🚨 FOUND 150 ROW LIMIT in file upload module!")

    except Exception as e:  # pragma: no cover - diagnostic helper
        print(f"❌ File upload module error: {e}")
        traceback.print_exc()
    print()

    print("📈 STEP 4: Testing analytics service data loading")
    try:
        loaded_data = load_service_data()

        print(f"✅ Analytics service found {len(loaded_data)} files")
        for filename, df in loaded_data.items():
            print(f"   {filename}: {len(df):,} rows")
            if len(df) == 150:
                print(f"   🚨 FOUND 150 ROW LIMIT in analytics service loading!")

    except Exception as e:
        print(f"❌ Analytics service loading error: {e}")
        traceback.print_exc()
    print()

    print("🧹 STEP 5: Testing column mapping and cleaning")
    try:
        cleaned_df = map_and_clean_df(original_df)
        print(f"✅ Column mapping: {len(cleaned_df):,} rows after cleaning")
        print(f"   Columns after mapping: {list(cleaned_df.columns)}")

        if len(cleaned_df) == 150:
            print(f"   🚨 FOUND 150 ROW LIMIT in column mapping!")
        elif len(cleaned_df) != len(original_df):
            print(
                f"   ⚠️  Row count changed: {len(original_df):,} → {len(cleaned_df):,}"
            )

    except Exception as e:
        print(f"❌ Column mapping error: {e}")
        traceback.print_exc()
    print()

    print("📊 STEP 6: Testing summarize_dataframe function")
    try:
        test_df = cleaned_df if "cleaned_df" in locals() else original_df
        summary = summarize_df(test_df)

        print("✅ Summary function results:")
        print(f"   Total events: {summary.get('total_events', 'N/A'):,}")
        print(f"   Active users: {summary.get('active_users', 'N/A'):,}")
        print(f"   Active doors: {summary.get('active_doors', 'N/A'):,}")

        if summary.get("total_events") == 150:
            print("   🚨 FOUND 150 ROW LIMIT in summarize_dataframe!")

    except Exception as e:
        print(f"❌ Summarize function error: {e}")
        traceback.print_exc()
    print()

    print("⚙️  STEP 7: Testing analytics service processing")
    try:
        result = run_analytics_processing()

        print("✅ Analytics processing results:")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Total events: {result.get('total_events', 'N/A'):,}")
        print(f"   Files processed: {result.get('files_processed', 'N/A')}")

        if result.get("total_events") == 150:
            print("   🚨 FOUND 150 ROW LIMIT in analytics processing!")

    except Exception as e:
        print(f"❌ Analytics processing error: {e}")
        traceback.print_exc()
    print()

    print("🔄 STEP 8: Testing chunked analytics")
    try:
        result = run_chunked_analytics(original_df)

        print(f"✅ Chunked analytics results:")
        print(f"   Total events: {result.get('total_events', 'N/A'):,}")
        print(f"   Rows processed: {result.get('rows_processed', 'N/A'):,}")
        print(f"   Unique users: {result.get('unique_users', 'N/A'):,}")

        if result.get("total_events") == 150 or result.get("rows_processed") == 150:
            print("   🚨 FOUND 150 ROW LIMIT in chunked analytics!")

    except Exception as e:
        print(f"❌ Chunked analytics error: {e}")
        traceback.print_exc()
    print()

    print("🔍 STEP 9: Searching for hardcoded 150 values")
    search_dirs = ["services", "analytics", "utils", "pages", "components"]
    found_150 = find_hardcoded_values(search_dirs)

    if found_150:
        print(f"✅ Found {len(found_150)} references to '150':")
        for ref in found_150[:10]:
            print(f"   {ref}")
        if len(found_150) > 10:
            print(f"   ... and {len(found_150) - 10} more")
    else:
        print("❌ No hardcoded '150' values found in Python files")
    print()

    print("🎯 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print("If you see '🚨 FOUND 150 ROW LIMIT' above, that's where the issue is!")
    print("If not, the 150 limit might be:")
    print("1. In a display/preview component (not actual processing)")
    print("2. In configuration files or environment variables")
    print("3. In the UI/dashboard display logic")
    print("4. A misunderstanding - check if analytics are actually processing all rows")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    test_complete_pipeline()
