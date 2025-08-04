#!/usr/bin/env python3
"""
Test Analytics Engine with rich learned mappings
"""

import asyncio
import json
import sys
from pathlib import Path

from yosai_intel_dashboard.src.infrastructure.config.app_config import UploadConfig

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from yosai_intel_dashboard.src.utils.text_utils import safe_text


async def test_analytics_with_mappings(verbose: bool = False) -> dict:
    try:
        print("=== TESTING ANALYTICS WITH LEARNED MAPPINGS ===")

        # Get the Enhanced Security Demo data and mappings
        # Process the parquet file using pandas directly
        import pandas as pd

        from yosai_intel_dashboard.src.services.analytics.analytics_service import (
            AnalyticsService,
        )
        from yosai_intel_dashboard.src.services.analytics.upload_analytics import (
            UploadAnalyticsProcessor,
        )
        from yosai_intel_dashboard.src.services.device_learning_service import (
            DeviceLearningService,
        )

        parquet_path = (
            Path(UploadConfig().folder) / "Enhanced_Security_Demo.csv.parquet"
        )

        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            print(f"Loaded Enhanced Security Demo: {len(df)} rows, {list(df.columns)}")

            # Get the learned mappings for this data
            device_service = DeviceLearningService()
            learned_mappings = device_service.learned_mappings

            enhanced_mappings = [
                (key, value)
                for key, value in learned_mappings.items()
                if "Enhanced_Security_Demo" in str(value.get("filename", ""))
            ]

            if enhanced_mappings:
                mapping_key, mapping_data = enhanced_mappings[0]
                print(f"Using learned mapping: {mapping_key}")
                print(f"Device count in mapping: {mapping_data.get('device_count', 0)}")

                device_mappings = mapping_data.get("device_mappings", {})
                print(f"Available device mappings: {len(device_mappings)}")

                result = {
                    "success": True,
                    "data_info": {
                        "rows": len(df),
                        "columns": list(df.columns),
                        "sample_doors": (
                            list(df["Door Location"].unique())[:5]
                            if "Door Location" in df.columns
                            else []
                        ),
                    },
                    "mapping_info": {
                        "mapping_key": mapping_key,
                        "device_count": mapping_data.get("device_count", 0),
                        "sample_devices": list(device_mappings.keys())[:5],
                    },
                }

                # Test AnalyticsService
                print("\n--- Testing AnalyticsService ---")
                try:
                    analytics_service = AnalyticsService()

                    # Test available methods
                    analytics_methods = [
                        method
                        for method in dir(analytics_service)
                        if not method.startswith("_")
                    ]
                    result["analytics_service"] = {
                        "available_methods": analytics_methods,
                        "health_check": (
                            analytics_service.health_check()
                            if hasattr(analytics_service, "health_check")
                            else "No health_check method"
                        ),
                    }
                    print(
                        f"AnalyticsService methods: {analytics_methods[:10]}..."
                    )  # Show first 10

                except Exception as e:
                    result["analytics_service"] = {"error": safe_text(e)}
                    print(f"AnalyticsService failed: {safe_text(e)}")

                # Test UploadAnalyticsProcessor
                print("\n--- Testing UploadAnalyticsProcessor ---")
                try:
                    upload_processor = UploadAnalyticsProcessor()

                    # Test available methods
                    upload_methods = [
                        method
                        for method in dir(upload_processor)
                        if not method.startswith("_")
                    ]
                    result["upload_analytics"] = {"available_methods": upload_methods}
                    print(
                        f"UploadAnalyticsProcessor methods: {upload_methods[:10]}..."
                    )  # Show first 10

                    # Try processing the dataframe if method exists
                    if hasattr(upload_processor, "process_dataframe"):
                        try:
                            analysis_result = upload_processor.process_dataframe(df)
                            result["upload_analytics"][
                                "analysis_result"
                            ] = analysis_result
                            print(
                                f"DataFrame analysis completed: {type(analysis_result)}"
                            )
                        except Exception as e:
                            result["upload_analytics"]["analysis_error"] = safe_text(e)
                            print(f"DataFrame analysis failed: {safe_text(e)}")

                except Exception as e:
                    result["upload_analytics"] = {"error": safe_text(e)}
                    print(f"UploadAnalyticsProcessor failed: {safe_text(e)}")

                # Test analytics functions from data_processing.analytics_engine
                print("\n--- Testing analytics engine functions ---")
                try:
                    from yosai_intel_dashboard.src.services import get_analytics_service

                    analytics_func = get_analytics_service()
                    result["analytics_engine_functions"] = {
                        "get_analytics_service": (
                            str(type(analytics_func)) if analytics_func else None
                        )
                    }
                    print(
                        f"Analytics engine functions loaded: {analytics_func is not None}"
                    )

                except Exception as e:
                    result["analytics_engine_functions"] = {"error": safe_text(e)}
                    print(f"Analytics engine functions failed: {safe_text(e)}")

                return result

            else:
                return {
                    "success": False,
                    "error": "No Enhanced Security Demo mappings found",
                }
        else:
            return {
                "success": False,
                "error": "Enhanced Security Demo parquet file not found",
            }

    except Exception as e:
        print(f"Error testing analytics: {safe_text(e)}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": safe_text(e)}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Test Analytics with learned mappings")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()
    result = asyncio.run(test_analytics_with_mappings(args.verbose))
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
