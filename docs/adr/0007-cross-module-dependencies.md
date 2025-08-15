# 0007: Cross-Module Dependency Documentation

## Status
Accepted

## Context
Cross-service data flow between the API, services and callback modules was
undocumented. Adding dependencies across these boundaries without review makes
the architecture difficult to reason about.

## Decision
All new dependencies between the `api`, `services` and `callbacks` packages
must include an Architecture Decision Record. A lightweight check script
(`scripts/architecture_review_check.py`) scans the repository for cross-module
imports and fails if such dependencies exist without a corresponding ADR.

## Consequences
Developers must document cross-module links and keep diagrams in
`docs/architecture` up to date. The check script runs in CI to guard against
undocumented architectural drift.
