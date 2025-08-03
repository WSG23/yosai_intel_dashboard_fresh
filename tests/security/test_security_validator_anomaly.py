from __future__ import annotations

import pandas as pd

from monitoring.anomaly_detector import AnomalyDetector
from yosai_intel_dashboard.src.core.security import SecurityAuditor, SecurityLevel


class DummyAccessModel:
    def get_data(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "user_id": ["u1"] * 5 + ["u2"] * 5,
                "source_ip": ["ip1"] * 5 + ["ip2"] * 5,
            }
        )


def test_anomaly_detector_flags_unusual_activity() -> None:
    detector = AnomalyDetector(access_model=DummyAccessModel())
    auditor = SecurityAuditor(anomaly_detector=detector)

    event = auditor.log_security_event(
        "login",
        SecurityLevel.LOW,
        {},
        source_ip="ip3",
        user_id="u3",
    )

    assert event.details["anomaly_flagged"] is True
    assert "anomaly_score" in event.details
    assert auditor.anomaly_metrics["anomalies"] == 1
    assert event.details["remediation_hint"].startswith("user exceeding")
