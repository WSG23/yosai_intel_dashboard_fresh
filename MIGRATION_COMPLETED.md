# Repository Migration Completed

The project has fully adopted the clean architecture layout under `yosai_intel_dashboard/src`.
All legacy top-level packages now symlink to their counterparts within this new
hierarchy. Import wrappers remain for backwards compatibility but new code
should import modules from the `yosai_intel_dashboard.src` package directly.

## Directory Moves

- `core/` → `yosai_intel_dashboard/src/core/`
- `models/` → `yosai_intel_dashboard/src/models/`
- `services/` → `yosai_intel_dashboard/src/services/`
- `config/` → `yosai_intel_dashboard/src/config/`
- `monitoring/` → `yosai_intel_dashboard/src/infrastructure/monitoring/`
- `security/` → `yosai_intel_dashboard/src/infrastructure/security/`
- `api/` → `yosai_intel_dashboard/src/api/`
- `plugins/` → `yosai_intel_dashboard/src/core/plugins/`

Symlinks matching the old paths were created to avoid breaking existing imports
while documentation and examples are updated to use the new modules.

## Import Wrappers

Thin wrapper modules (e.g. `core/service_container.py`) re-export classes from
the new locations. These wrappers will be kept until the next major release to
make upgrading smoother for downstream projects.

## Remaining Technical Debt

Some tests still rely on the wrapper modules and should be refactored.
Validation of the symlinked directories on Windows is incomplete and may require
additional CI adjustments.
