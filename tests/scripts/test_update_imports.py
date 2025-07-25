import textwrap
from pathlib import Path

from scripts.update_imports import main, update_file


def _run_update(tmp_path: Path, content: str) -> str:
    target = tmp_path / "sample.py"
    target.write_text(textwrap.dedent(content))
    update_file(target)
    return target.read_text()


def test_update_imports_patterns(tmp_path: Path) -> None:
    before = """
    from yosai_intel_dashboard.src.infrastructure.config.utils import a
    import yosai_intel_dashboard.src.infrastructure.config.utils
    from yosai_intel_dashboard.src.infrastructure.monitoring.metrics import b
    import yosai_intel_dashboard.src.infrastructure.monitoring.metrics
    from yosai_intel_dashboard.src.infrastructure.security.auth import c
    import yosai_intel_dashboard.src.infrastructure.security.helpers
    from yosai_intel_dashboard.src.adapters.api.client import d
    import yosai_intel_dashboard.src.adapters.api.client
    from yosai_intel_dashboard.src.adapters.api.plugins.extra import e
    import yosai_intel_dashboard.src.adapters.api.plugins.extra
    """
    after = """
    from yosai_intel_dashboard.src.infrastructure.config.utils import a
    import yosai_intel_dashboard.src.infrastructure.config.utils
    from yosai_intel_dashboard.src.infrastructure.monitoring.metrics import b
    import yosai_intel_dashboard.src.infrastructure.monitoring.metrics
    from yosai_intel_dashboard.src.infrastructure.security.auth import c
    import yosai_intel_dashboard.src.infrastructure.security.helpers
    from yosai_intel_dashboard.src.adapters.api.client import d
    import yosai_intel_dashboard.src.adapters.api.client
    from yosai_intel_dashboard.src.adapters.api.plugins.extra import e
    import yosai_intel_dashboard.src.adapters.api.plugins.extra
    """
    result = _run_update(tmp_path, before)
    assert result == textwrap.dedent(after)


def test_update_imports_cli(tmp_path: Path) -> None:
    file_path = tmp_path / "example.py"
    file_path.write_text(
        "from yosai_intel_dashboard.src.infrastructure.config import x\n"
    )
    main([str(tmp_path)])
    expected = "from yosai_intel_dashboard.src.infrastructure.config import x\n"
    assert file_path.read_text() == expected
