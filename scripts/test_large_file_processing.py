def test_large_file_processing():
    import pandas as pd

    from yosai_intel_dashboard.src.services.analytics_service import AnalyticsService

    # Create a test dataframe similar to your data
    test_df = pd.DataFrame(
        {
            "person_id": [f"user_{i}" for i in range(100000)],
            "door_id": [f"door_{i%100}" for i in range(100000)],
            "access_result": [
                "Granted" if i % 3 == 0 else "Denied" for i in range(100000)
            ],
            "timestamp": pd.date_range("2024-01-01", periods=100000, freq="1min"),
        }
    )

    service = AnalyticsService()

    # Test diagnosis first
    diagnosis = service.diagnose_data_flow(test_df)
    print("Diagnosis:", diagnosis)

    # Test actual processing
    result = service.analyze_with_chunking(
        test_df, ["security", "trends", "anomaly", "behavior"]
    )
    print(f"Processed {result.get('rows_processed', 'unknown')} rows")
    print(f"Total events: {result.get('total_events', 0)}")


if __name__ == "__main__":
    test_large_file_processing()
