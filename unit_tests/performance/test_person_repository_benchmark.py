from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import time
from pathlib import Path

import pytest

_loader = importlib.machinery.SourceFileLoader(
    "person_repo", str(Path("repositories/person_repository.py"))
)
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
person_repo = importlib.util.module_from_spec(_spec)
sys.modules[_loader.name] = person_repo
_loader.exec_module(person_repo)

InMemoryPersonRepository = person_repo.InMemoryPersonRepository
Person = person_repo.Person


class PersonRepositoryBenchmark:
    def __init__(self, num_people: int = 1000) -> None:
        self.num_people = num_people

    def run(self) -> float:
        repo = InMemoryPersonRepository()
        start = time.perf_counter()
        for i in range(self.num_people):
            person = Person(person_id=str(i), name=f"Name {i}", department="D")
            repo.save(person)
        end = time.perf_counter()
        total = end - start
        print(f"Saved {self.num_people} people in {total:.4f} seconds")
        return total


BENCHMARK_THRESHOLD_SECONDS = 0.5


def test_inmemory_person_repository_benchmark_threshold() -> None:
    bench = PersonRepositoryBenchmark()
    total = bench.run()
    assert total <= BENCHMARK_THRESHOLD_SECONDS, (
        f"Saving {bench.num_people} people took {total:.4f}s, "
        f"exceeding threshold {BENCHMARK_THRESHOLD_SECONDS}s"
    )
