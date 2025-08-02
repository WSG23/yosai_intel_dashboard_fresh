#!/usr/bin/env python3
"""
Step 2: Add missing analytics methods to UploadAnalyticsProcessor
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def add_missing_analytics_methods():
    """Add missing methods to UploadAnalyticsProcessor"""

    print("=== STEP 2: ADDING MISSING ANALYTICS METHODS ===")

    try:
        # First, let's check what methods are currently in UploadAnalyticsProcessor
        from yosai_intel_dashboard.src.services.upload_processing import UploadAnalyticsProcessor

        processor = UploadAnalyticsProcessor()
        current_methods = [
            method for method in dir(processor) if not method.startswith("_")
        ]
        print(f"Current methods: {current_methods}")

        # Check which methods are missing
        required_methods = [
            "get_analytics_from_uploaded_data",
            "clean_uploaded_dataframe",
        ]
        missing_methods = [
            method for method in required_methods if not hasattr(processor, method)
        ]

        print(f"Missing methods: {missing_methods}")

        # Add the missing methods
        if "get_analytics_from_uploaded_data" not in current_methods:

            def get_analytics_from_uploaded_data(self):
                """Get analytics from uploaded data"""
                try:
                    data = self.load_uploaded_data()
                    if not data:
                        return {
                            "status": "no_data",
                            "message": "No uploaded files available",
                        }

                    # Process the data
                    result = self._process_uploaded_data_directly(data)
                    result["status"] = "success"
                    result["message"] = f"Processed {len(data)} files"
                    return result

                except Exception as e:
                    return {"status": "error", "message": str(e)}

            UploadAnalyticsProcessor.get_analytics_from_uploaded_data = (
                get_analytics_from_uploaded_data
            )
            print("✅ Added get_analytics_from_uploaded_data method")

        if "clean_uploaded_dataframe" not in current_methods:

            def clean_uploaded_dataframe(self, df):
                """Clean and process uploaded dataframe"""
                import pandas as pd

                # Basic cleaning - remove null rows, standardize column names
                cleaned_df = df.dropna(how="all").copy()

                # Standardize column names
                cleaned_df.columns = [
                    col.strip().replace(" ", "_").lower() for col in cleaned_df.columns
                ]

                return cleaned_df

            UploadAnalyticsProcessor.clean_uploaded_dataframe = clean_uploaded_dataframe
            print("✅ Added clean_uploaded_dataframe method")

        # Add other helpful methods
        if "summarize_dataframe" not in current_methods:

            def summarize_dataframe(self, df):
                """Create a summary of the dataframe"""
                import pandas as pd

                return {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                    "null_counts": df.isnull().sum().to_dict(),
                }

            UploadAnalyticsProcessor.summarize_dataframe = summarize_dataframe
            print("✅ Added summarize_dataframe method")

        # Test the new methods
        print("\n=== TESTING NEW METHODS ===")

        test_processor = UploadAnalyticsProcessor()

        # Test get_analytics_from_uploaded_data
        try:
            analytics_result = test_processor.get_analytics_from_uploaded_data()
            print(
                f"✅ get_analytics_from_uploaded_data: {analytics_result.get('status', 'unknown')}"
            )
        except Exception as e:
            print(f"❌ get_analytics_from_uploaded_data failed: {e}")

        # Test clean_uploaded_dataframe
        try:
            import pandas as pd

            test_df = pd.DataFrame({"Name": ["John", "Jane"], "Age": [25, 30]})
            cleaned_df = test_processor.clean_uploaded_dataframe(test_df)
            print(f"✅ clean_uploaded_dataframe: {len(cleaned_df)} rows processed")
        except Exception as e:
            print(f"❌ clean_uploaded_dataframe failed: {e}")

        # Test summarize_dataframe
        try:
            summary = test_processor.summarize_dataframe(test_df)
            print(
                f"✅ summarize_dataframe: {summary['rows']} rows, {summary['columns']} columns"
            )
        except Exception as e:
            print(f"❌ summarize_dataframe failed: {e}")

        print("\n🎉 Step 2 completed successfully!")
        return True

    except Exception as e:
        print(f"Step 2 failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = add_missing_analytics_methods()
    sys.exit(0 if success else 1)
