from __future__ import annotations

import types


def test_core_integrations_reexport() -> None:
    import core

    assert isinstance(core.integrations, types.ModuleType)
    assert "export_to_stix" in core.integrations.__all__
