from tools.organize_imports import ImportOrganizer


def test_organizer_adds_future_typing_and_backup(tmp_path):
    content = (
        "def fetch_from_db(conn) -> List[int]:\n"
        "    return [1]\n\n"
        "def call_external_api(url: str) -> Dict[str, Any]:\n"
        "    return {'url': url}\n\n"
        "def process_service(data: str) -> None:\n"
        "    pass\n"
    )
    file_path = tmp_path / "sample.py"
    file_path.write_text(content)

    organizer = ImportOrganizer()
    changed = organizer.organize_file(file_path)
    assert changed is True

    new_text = file_path.read_text()
    assert new_text.startswith("from __future__ import annotations\n")
    assert "from typing import Any, Dict, List" in new_text
    assert "def fetch_from_db(conn) -> List[int]:" in new_text
    assert "def call_external_api(url: str) -> Dict[str, Any]:" in new_text
    assert "def process_service(data: str) -> None:" in new_text

    backup_path = file_path.with_suffix(".py.bak")
    assert backup_path.exists()
    assert backup_path.read_text() == content


def test_organizer_no_changes_when_not_needed(tmp_path):
    content = (
        "from __future__ import annotations\n\n"
        "def existing() -> int:\n"
        "    return 1\n"
    )
    file_path = tmp_path / "clean.py"
    file_path.write_text(content)

    organizer = ImportOrganizer()
    changed = organizer.organize_file(file_path)
    assert changed is False
    assert file_path.read_text() == content
    assert not file_path.with_suffix(".py.bak").exists()
