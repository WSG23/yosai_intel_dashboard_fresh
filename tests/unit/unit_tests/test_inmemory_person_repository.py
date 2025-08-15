from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path

_loader = importlib.machinery.SourceFileLoader(
    "person_repo", str(Path("repositories/person_repository.py"))
)
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
person_repo = importlib.util.module_from_spec(_spec)
sys.modules[_loader.name] = person_repo
_loader.exec_module(person_repo)

InMemoryPersonRepository = person_repo.InMemoryPersonRepository
Person = person_repo.Person
failure = person_repo.failure


def test_save_and_retrieve_person():
    repo = InMemoryPersonRepository()
    person = Person(person_id="1", name="Alice", department="Engineering")
    save_result = repo.save(person)
    assert save_result.is_success() and save_result.value == person

    fetched = repo.find_by_id("1")
    assert fetched.is_success() and fetched.value == person

    dept_result = repo.find_by_department("Engineering")
    assert dept_result.is_success() and dept_result.value == [person]


def test_save_returns_failure_on_validation(monkeypatch):
    repo = InMemoryPersonRepository()
    person = Person(person_id="2")

    def fake_validate(self):
        return failure("boom")

    monkeypatch.setattr(Person, "validate", fake_validate)
    result = repo.save(person)
    assert result.is_failure() and result.error == "Invalid person: boom"
