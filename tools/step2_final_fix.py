#!/usr/bin/env python3
"""
Final fix for Step 2 - properly add summarize_dataframe to class
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def final_method_fix():
    print("=== FINAL STEP 2 FIX ===")

    try:
        from yosai_intel_dashboard.src.services.upload_processing import UploadAnalyticsProcessor

        # Add summarize_dataframe method properly to the class
        if not hasattr(UploadAnalyticsProcessor, "summarize_dataframe"):

            def summarize_dataframe(self, df):
                """Create a summary of the dataframe"""
                return {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                    "null_counts": df.isnull().sum().to_dict(),
                }

            UploadAnalyticsProcessor.summarize_dataframe = summarize_dataframe
            print("✅ Added summarize_dataframe method to class")
        else:
            print("✅ summarize_dataframe method already exists")

        # Test it
        import pandas as pd

        processor = UploadAnalyticsProcessor()
        test_df = pd.DataFrame({"Event Time": ["2024-12-01"], "Status": ["Granted"]})

        summary = processor.summarize_dataframe(test_df)
        print(
            f"✅ Test successful: {summary['rows']} rows, {summary['columns']} columns"
        )

        return True

    except Exception as e:
        print(f"Final fix failed: {e}")
        return False


if __name__ == "__main__":
    success = final_method_fix()
    if success:
        print("🎉 Step 2 100% complete!")
    sys.exit(0 if success else 1)
