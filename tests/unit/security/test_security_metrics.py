from prometheus_client import generate_latest
from prometheus_client.parser import text_string_to_metric_families

import validation.security_validator as val_mod


class DummyValidator:
    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - simple stub
        pass


val_mod.SecurityValidator = DummyValidator
val_mod.redis_client = None

from yosai_intel_dashboard.src.core.security import SecurityLevel
from yosai_intel_dashboard.src.infrastructure.security.reporting import (
    _get_auditor,
    generate_report,
    report_to_html,
)


def test_report_structure_and_remediation():
    auditor = _get_auditor()
    auditor.events = []

    auditor.log_security_event(
        "input_validation_failed",
        SecurityLevel.HIGH,
        {"issues": ["xss", "sql_injection"]},
    )
    auditor.log_security_event("login_failure", SecurityLevel.MEDIUM, {})

    report = generate_report(hours=24)
    assert report["summary"]["violations"]["xss"] == 1
    assert report["summary"]["violations"]["sql_injection"] == 1
    assert "parameterized" in report["remediation"]["sql_injection"]

    html = report_to_html(report)
    assert "<html>" in html.lower()

    metrics = generate_latest().decode()
    violation_ok = False
    event_ok = False
    for fam in text_string_to_metric_families(metrics):
        if fam.name == "security_violations_total":
            for sample in fam.samples:
                if sample.labels.get("issue") == "xss" and sample.value == 1.0:
                    violation_ok = True
        if fam.name == "security_events_total":
            for sample in fam.samples:
                if (
                    sample.labels.get("type") == "login_failure"
                    and sample.labels.get("severity") == "medium"
                    and sample.value == 1.0
                ):
                    event_ok = True
    assert violation_ok and event_ok
