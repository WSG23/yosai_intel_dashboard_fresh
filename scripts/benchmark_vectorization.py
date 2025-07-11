import timeit

import pandas as pd

from analytics.anomaly_detection import AnomalyDetector
from analytics.security_patterns import SecurityPatternsAnalyzer


def generate_sample_df(n=10000):
    return pd.DataFrame(
        {
            "event_id": range(n),
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="min"),
            "person_id": [f"u{i%50}" for i in range(n)],
            "door_id": [f"d{i%10}" for i in range(n)],
            "access_result": ["Denied" if i % 3 else "Granted" for i in range(n)],
        }
    )


def benchmark():
    df = generate_sample_df()
    analyzer = SecurityPatternsAnalyzer()
    df = analyzer._prepare_data(df)
    detection = AnomalyDetector()

    t1 = timeit.timeit(lambda: analyzer._extract_failure_patterns(df), number=5)
    t2 = timeit.timeit(lambda: analyzer._identify_timing_patterns(df), number=5)
    t3 = timeit.timeit(lambda: detection._detect_frequency_anomalies(df), number=5)
    print("Failure patterns:", t1)
    print("Timing patterns:", t2)
    print("Frequency anomalies:", t3)


if __name__ == "__main__":
    benchmark()
