from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_diagnose_cli_runs(tmp_path, capsys):
    script = Path(__file__).resolve().parents[2] / "tools" / "diagnose_upload_config.py"
    mod_dir = tmp_path / "config"
    mod_dir.mkdir()
    (mod_dir / "__init__.py").write_text("")
    (mod_dir / "dynamic_config.py").write_text(
        "def diagnose_upload_config():\n"
        "    print('=== Upload Configuration Diagnosis ===')\n"
        "dynamic_config = type('D', (), {\n"
        "    'get_upload_chunk_size': lambda self: 1,\n"
        "    'get_max_parallel_uploads': lambda self: 2,\n"
        "    'get_validator_rules': lambda self: {}\n"
        "})()\n"
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path)

    res = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, env=env
    )
    print(res.stdout)
    out = capsys.readouterr().out
    assert "Upload Configuration Diagnosis" in out

    res = subprocess.run(
        [sys.executable, str(script), "--verbose"],
        capture_output=True,
        text=True,
        env=env,
    )
    print(res.stdout)
    out = capsys.readouterr().out
    assert "Verbose Details" in out
