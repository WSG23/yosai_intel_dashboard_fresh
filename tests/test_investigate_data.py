import builtins
import json
import os
from pathlib import Path

import pytest

import investigate_data


def test_file_info_reading_uses_utf8(monkeypatch, tmp_path):
    os.environ["UPLOAD_FOLDER"] = str(tmp_path)
    info = {"föö.csv": {"rows": 1, "columns": 2, "size_mb": 0.1}}
    info_file = tmp_path / "file_info.json"
    info_file.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")

    called_encodings = []
    original_open = builtins.open

    def fake_open(file, mode="r", *args, **kwargs):
        if Path(file).name == "file_info.json":
            called_encodings.append(kwargs.get("encoding"))
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    # Should not raise and should call open with utf-8 encoding
    investigate_data.investigate_data()
    assert "utf-8" in called_encodings
