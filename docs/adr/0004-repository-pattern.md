# ADR 0004: Repository Pattern

## Context
Data access logic was scattered across services, coupling business code to specific storage implementations.

## Decision
Apply the Repository pattern to abstract persistence behind interfaces. Concrete repositories implement data access for each entity while clients depend on interfaces.

Recent updates added repositories for file system and database access:

- ``FeatureFlagCacheRepository`` persists feature flag caches.
- ``FileRepository`` handles file reads and writes for export services.
- ``DBHealthRepository`` encapsulates database health checks.
- ``RequirementsRepository`` loads package specifications for dependency
  verification.

Services receive these repositories via constructor injection, enabling easy mocking in unit tests.

Example usage::

    from repository.requirements import FileRequirementsRepository
    from utils.dependency_checker import DependencyChecker

    checker = DependencyChecker(FileRequirementsRepository(Path("requirements.txt")))
    checker.verify_requirements()

## Consequences
- Business logic remains storage agnostic.
- Easier to swap or mock data sources in tests.
- Requires extra boilerplate for simple queries.
