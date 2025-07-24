# Clean Architecture Directory Structure

This repository now follows a simplified Clean Architecture layout. The top level
`yosai_intel_dashboard/` package contains all runtime code and is subdivided into
four layers:

- **core** – business rules and domain logic. This layer has no dependencies on
  frameworks or external services.
- **adapters** – interface adapters such as REST controllers and database
  mappers. They translate external input into the core model.
- **infrastructure** – framework and tool specific code. Configuration,
  monitoring and security implementations live here.
- **services** – deployable microservices built on top of the other layers.

```
yosai_intel_dashboard/
├── src/
│   ├── core/
│   │   ├── domain/
│   │   ├── use_cases/
│   │   └── interfaces/
│   ├── adapters/
│   │   ├── api/
│   │   ├── persistence/
│   │   └── ui/
│   ├── infrastructure/
│   │   ├── config/
│   │   ├── security/
│   │   └── monitoring/
│   └── services/
│       ├── analytics/
│       ├── events/
│       └── ml/
├── tests/
├── scripts/
├── deploy/
│   ├── docker/
│   ├── k8s/
│   └── helm/
└── docs/
```

The `tests` directory mirrors the layout under `src`. During the transition the
legacy modules remain in place but import wrappers re-export them from the new
packages. See `scripts/migrate_to_clean_arch.py` for an automated migration.
