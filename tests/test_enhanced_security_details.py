from yosai_intel_dashboard.src.services.analytics.core.utils.results_display import _extract_enhanced_security_details


def test_extract_enhanced_security_details_basic():
    results = {
        "threat_count": 5,
        "critical_threats": 2,
        "confidence_interval": (80.5, 90.2),
        "recommendations": ["Update policies", "Review logs"],
        "threats": [
            {
                "type": "brute force",
                "severity": "critical",
                "confidence": 0.95,
                "description": "Multiple failed logins",
            },
            {
                "type": "tailgating",
                "severity": "medium",
                "confidence": 0.7,
                "description": "Piggybacking events",
            },
            {
                "type": "unknown card",
                "severity": "high",
                "confidence": 0.9,
                "description": "Unknown badges",
            },
            {
                "type": "door forced",
                "severity": "critical",
                "confidence": 0.85,
                "description": "Door forced open",
            },
        ],
    }
    details = _extract_enhanced_security_details(results)
    assert details["threat_count"] == 5
    assert details["critical_threats"] == 2
    assert details["confidence_interval"] == (80.5, 90.2)
    assert details["recommendations"] == ["Update policies", "Review logs"]
    assert details["top_threats"][0].startswith("Critical")
    assert len(details["top_threats"]) == 3


def test_extract_enhanced_security_details_defaults():
    results = {
        "threats": [
            {"severity": "low", "confidence": 0.2, "description": "test1"},
            {"severity": "critical", "confidence": 0.9, "description": "test2"},
        ]
    }
    details = _extract_enhanced_security_details(results)
    assert details["threat_count"] == 2
    assert details["critical_threats"] == 1
    assert details["confidence_interval"] == (0.0, 0.0)
    assert details["recommendations"] == []
    assert details["top_threats"][0].startswith("Critical")
