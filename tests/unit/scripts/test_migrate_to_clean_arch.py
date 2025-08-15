from pathlib import Path

import scripts.migrate_to_clean_arch as mig


def _setup_repo(tmp_path: Path) -> None:
    for name in [
        "core",
        "models",
        "services",
        "config",
        "monitoring",
        "security",
        "api",
        "plugins",
    ]:
        d = tmp_path / name
        d.mkdir(parents=True)
        (d / "__init__.py").write_text("")


def test_dry_run(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    monkeypatch.setattr(mig, "ROOT", tmp_path)
    monkeypatch.setattr(mig, "SRC_ROOT", tmp_path / "yosai_intel_dashboard" / "src")
    mig.main(["--dry-run"])
    assert (tmp_path / "core").is_dir()
    assert not (tmp_path / "yosai_intel_dashboard" / "src" / "core").exists()


def test_backup_and_rollback(tmp_path: Path, monkeypatch) -> None:
    _setup_repo(tmp_path)
    archive = tmp_path / "backup.tar.gz"
    monkeypatch.setattr(mig, "ROOT", tmp_path)
    monkeypatch.setattr(mig, "SRC_ROOT", tmp_path / "yosai_intel_dashboard" / "src")
    monkeypatch.setattr(mig.subprocess, "run", lambda *a, **k: None)
    mig.main(["--backup", str(archive)])
    assert (tmp_path / "core.py").exists()
    assert (tmp_path / "yosai_intel_dashboard" / "src" / "core").is_dir()
    mig.main(["--rollback", str(archive)])
    assert (tmp_path / "core").is_dir()
    assert not (tmp_path / "core.py").exists()
    assert not (tmp_path / "yosai_intel_dashboard" / "src" / "core").exists()


def test_report(tmp_path: Path, monkeypatch, capsys) -> None:
    _setup_repo(tmp_path)
    dst = tmp_path / "yosai_intel_dashboard" / "src" / "core"
    dst.mkdir(parents=True)
    monkeypatch.setattr(mig, "ROOT", tmp_path)
    monkeypatch.setattr(mig, "SRC_ROOT", tmp_path / "yosai_intel_dashboard" / "src")
    mig.main(["--report"])
    out = capsys.readouterr().out
    assert "Migrated 1 of" in out
