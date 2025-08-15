from dataclasses import FrozenInstanceError

import pytest

from yosai_intel_dashboard.src.adapters.api.plugins.compliance_plugin.config import (
    ComplianceConfig,
)


def test_compliance_config_is_immutable():
    config = ComplianceConfig.from_dict({"audit_retention_days": 10})
    with pytest.raises(FrozenInstanceError):
        config.audit_retention_days = 5


def test_compliance_config_ignores_invalid_keys():
    config = ComplianceConfig.from_dict({"nonexistent": 123})
    assert not hasattr(config, "nonexistent")
