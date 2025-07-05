#!/usr/bin/env python3
"""
Debug CSV truncation issue - trace where 2.5MB becomes 150 rows
"""
import pandas as pd
import base64
import io
import logging
from pathlib import Path

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def debug_csv_processing():
    """Debug the entire CSV processing pipeline"""

    print("🔍 DEBUGGING CSV TRUNCATION ISSUE")
    print("=" * 60)

    # Step 1: Check if there's already a CSV file to test with
    csv_path = "temp/uploaded_data/Demo3_data_copy.csv.parquet"
    if Path(csv_path).exists():
        print(f"📁 Found existing file: {csv_path}")
        try:
            df = pd.read_parquet(csv_path)
            print(f"   Parquet file contains: {len(df):,} rows")
        except Exception as e:
            print(f"   Error reading parquet: {e}")

    # Step 2: Test CSV processing directly
    print(f"\n🧪 TESTING CSV PROCESSING PIPELINE")

    # Test with a known large CSV (create a test one)
    print(f"📝 Creating test CSV with 1000 rows...")
    test_data = []
    for i in range(1000):
        test_data.append(
            {
                "Timestamp": f"1/21/25 {i:02d}:14",
                "Person ID": f"P{430404 + i}",
                "Token ID": f"T{430404 + i}",
                "Device name": f"F01C Door {i % 10}",
                "Access result": "Access Granted" if i % 2 == 0 else "Access Denied",
            }
        )

    test_df = pd.DataFrame(test_data)
    print(f"✅ Created test DataFrame: {len(test_df):,} rows")

    # Step 3: Test each stage of processing
    test_stages(test_df)

    # Step 4: Check actual file upload processing
    print(f"\n🔄 TESTING ACTUAL UPLOAD PROCESSING")
    test_upload_pipeline()


def test_stages(test_df):
    """Test each stage of DataFrame processing"""

    print(f"\n📊 STAGE 1: Raw DataFrame")
    print(f"   Rows: {len(test_df):,}")

    # Stage 2: Test Unicode cleaning
    print(f"\n🧹 STAGE 2: Unicode Processing")
    try:
        from core.unicode_processor import sanitize_data_frame

        cleaned_df = sanitize_data_frame(test_df)
        print(f"   After unicode cleaning: {len(cleaned_df):,} rows")
        if len(cleaned_df) != len(test_df):
            print(f"   ⚠️  TRUNCATION DETECTED in unicode processing!")
            return cleaned_df
    except Exception as e:
        print(f"   Error in unicode processing: {e}")
        cleaned_df = test_df

    # Stage 3: Test security validation
    print(f"\n🔒 STAGE 3: Security Validation")
    try:
        from security.dataframe_validator import DataFrameSecurityValidator

        validator = DataFrameSecurityValidator()
        validated_df = validator.validate_for_upload(cleaned_df)
        print(f"   After security validation: {len(validated_df):,} rows")
        if len(validated_df) != len(cleaned_df):
            print(f"   ⚠️  TRUNCATION DETECTED in security validation!")
            return validated_df
    except Exception as e:
        print(f"   Error in security validation: {e}")
        validated_df = cleaned_df

    # Stage 4: Test file processing
    print(f"\n📄 STAGE 4: File Processing")
    try:
        # Save to CSV and reload to simulate upload
        csv_content = validated_df.to_csv(index=False)
        print(f"   CSV content size: {len(csv_content):,} bytes")

        # Test pandas read_csv directly
        reloaded_df = pd.read_csv(io.StringIO(csv_content))
        print(f"   After CSV reload: {len(reloaded_df):,} rows")
        if len(reloaded_df) != len(validated_df):
            print(f"   ⚠️  TRUNCATION DETECTED in CSV reload!")
            return reloaded_df

    except Exception as e:
        print(f"   Error in file processing: {e}")
        reloaded_df = validated_df

    print(f"✅ No truncation detected in standard processing pipeline")
    return reloaded_df


def test_upload_pipeline():
    """Test the actual upload processing pipeline"""

    # Create test CSV content as base64 (simulating file upload)
    test_csv = """Timestamp,Person ID,Token ID,Device name,Access result
1/21/25 01:14,P430404,T430404,F01C Staircase C,Access Granted
1/21/25 03:29,P943512,T943512,F01C Staircase C,Access Granted
1/21/25 04:53,P080151,T080151,F01A Telecom room 2,Access Granted"""

    # Add many more rows to test truncation
    for i in range(4, 200):
        test_csv += f"\n1/21/25 {i:02d}:14,P{430404 + i},T{430404 + i},F01C Door {i % 10},Access Granted"

    print(f"📄 Test CSV created with ~200 rows")
    print(f"   Size: {len(test_csv):,} bytes")

    # Encode as base64 (simulating browser upload)
    encoded = base64.b64encode(test_csv.encode()).decode()
    contents = f"data:text/csv;base64,{encoded}"

    # Test the actual upload processing
    try:
        from services.upload_service import process_uploaded_file

        result = process_uploaded_file(contents, "test_large.csv")

        if result.get("success"):
            df = result.get("data")
            if df is not None:
                print(f"   📊 Upload processing result: {len(df):,} rows")
                if len(df) < 180:  # Should be close to 200
                    print(f"   🚨 TRUNCATION DETECTED in upload processing!")
                    print(f"   Expected: ~200 rows, Got: {len(df)} rows")

                    # Check if there's a row limit in the processing
                    print(f"   🔍 Investigating upload service...")

                else:
                    print(f"   ✅ No truncation in upload processing")
            else:
                print(f"   ❌ No DataFrame returned from upload processing")
        else:
            print(f"   ❌ Upload processing failed: {result.get('error')}")

    except Exception as e:
        print(f"   ❌ Error testing upload pipeline: {e}")

    # Also test file validator directly
    try:
        from utils.file_validator import safe_decode_file, process_dataframe

        decoded = safe_decode_file(contents)
        if decoded:
            print(f"   📦 Decoded size: {len(decoded):,} bytes")
            df, error = process_dataframe(decoded, "test_large.csv")
            if df is not None:
                print(f"   📊 File validator result: {len(df):,} rows")
                if len(df) < 180:
                    print(f"   🚨 TRUNCATION DETECTED in file validator!")
            else:
                print(f"   ❌ File validator error: {error}")
        else:
            print(f"   ❌ Failed to decode file contents")

    except Exception as e:
        print(f"   ❌ Error testing file validator: {e}")


def check_environment_limits():
    """Check for any environment variables that might limit processing"""

    print(f"\n🌍 CHECKING ENVIRONMENT LIMITS")

    try:
        from config.dynamic_config import dynamic_config

        print(f"   Upload limit: {dynamic_config.security.max_upload_mb}MB")
        if hasattr(dynamic_config.security, "max_file_size_mb"):
            print(f"   File size limit: {dynamic_config.security.max_file_size_mb}MB")
        if hasattr(dynamic_config, "analytics"):
            if hasattr(dynamic_config.analytics, "max_records_per_query"):
                print(
                    f"   Max records per query: {dynamic_config.analytics.max_records_per_query:,}"
                )
            if hasattr(dynamic_config.analytics, "chunk_size"):
                print(f"   Chunk size: {dynamic_config.analytics.chunk_size:,}")

    except Exception as e:
        print(f"   ❌ Error checking config: {e}")


if __name__ == "__main__":
    debug_csv_processing()
    check_environment_limits()

    print(f"\n" + "=" * 60)
    print(f"🎯 NEXT STEPS:")
    print(f"1. Look for any 'head(150)' or 'nrows=150' in the codebase")
    print(f"2. Check if there's a sampling configuration")
    print(f"3. Enable debug logging and re-upload your 2.5MB file")
    print(f"4. Check the actual upload logs for truncation messages")
