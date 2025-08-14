from __future__ import annotations

from repositories.person_repository import InMemoryPersonRepository, Person


def test_find_by_id_missing_returns_none() -> None:
    repo = InMemoryPersonRepository()
    result = repo.find_by_id("missing")
    assert result.is_success() and result.value is None


def test_find_by_id_failure_on_exception(monkeypatch) -> None:
    repo = InMemoryPersonRepository()

    class Broken(dict):
        def get(self, *args, **kwargs):  # type: ignore[override]
            raise RuntimeError("boom")

    repo._people = Broken()
    result = repo.find_by_id("1")
    assert result.is_failure() and "boom" in result.error


def test_find_by_department_failure(monkeypatch) -> None:
    repo = InMemoryPersonRepository()

    class Broken(dict):
        def values(self):  # type: ignore[override]
            raise RuntimeError("fail")

    repo._people = Broken()
    result = repo.find_by_department("eng")
    assert result.is_failure() and "fail" in result.error


def test_save_failure_on_storage_error(monkeypatch) -> None:
    repo = InMemoryPersonRepository()
    p = Person(person_id="1")

    class Broken(dict):
        def __setitem__(self, key, value):  # type: ignore[override]
            raise RuntimeError("storage")

    repo._people = Broken()
    result = repo.save(p)
    assert result.is_failure() and "storage" in result.error

