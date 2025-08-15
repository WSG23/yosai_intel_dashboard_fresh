from __future__ import annotations

import json
import time

import pandas as pd
import pytest


SCHEDULED_DELETIONS_THRESHOLD_SECONDS = 0.1


def original_process(df: pd.DataFrame) -> int:
    processed = 0
    for _, row in df.iterrows():
        consent = json.loads(row["consent_status"])
        for _ in consent.get("scheduled_deletion", {}).get(
            "data_types", ["biometric_templates"]
        ):
            processed += 1
    return processed


def optimized_process(df: pd.DataFrame) -> int:
    processed = 0
    for row in df.itertuples(index=False):
        consent = json.loads(row.consent_status)
        processed += sum(
            1
            for _ in consent.get("scheduled_deletion", {}).get(
                "data_types", ["biometric_templates"]
            )
        )
    return processed


@pytest.mark.performance
def test_process_scheduled_deletions_benchmark():
    records = 1000
    df = pd.DataFrame(
        {
            "person_id": [f"user{i}" for i in range(records)],
            "consent_status": [
                json.dumps(
                    {"scheduled_deletion": {"data_types": ["biometric_templates"]}}
                )
            ]
            * records,
        }
    )
    start = time.time()
    baseline = original_process(df)
    original_duration = time.time() - start

    start = time.time()
    optimized = optimized_process(df)
    optimized_duration = time.time() - start

    assert baseline == optimized
    assert optimized_duration <= original_duration
    assert optimized_duration <= SCHEDULED_DELETIONS_THRESHOLD_SECONDS, (
        f"Optimized processing took {optimized_duration:.4f}s, "
        f"expected <= {SCHEDULED_DELETIONS_THRESHOLD_SECONDS}s"
    )
