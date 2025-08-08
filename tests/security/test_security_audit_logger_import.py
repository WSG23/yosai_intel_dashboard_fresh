from __future__ import annotations

import importlib
import inspect


def test_security_audit_logger_imports_real_core_integrations():
    from yosai_intel_dashboard.src.infrastructure.security import (  # noqa: F401
        SecurityAuditLogger,
    )

    module = importlib.import_module(
        "yosai_intel_dashboard.src.core.integrations.siem_connectors"
    )
    func_file = inspect.getsourcefile(module.send_to_siem)
    assert func_file and func_file.endswith("core/integrations/siem_connectors.py")
