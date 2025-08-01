# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial changelog with standard sections.
- Database migration `0003` adds `ml_models` table for the model registry.

### Changed
- Updated `run_service_analysis` to use `analyze_data_with_service` and
  `create_analysis_results_display`.

### Fixed
- Navigation bar icons failed to load when `app.get_asset_url` returned
  `None`. Asset utilities now fall back to direct `/assets/` paths.
- Removed unused "Use Camera" button from the file upload component.
- Reduced `.nav-icon` size to `2rem` for better appearance with fallback
  Font Awesome icons.


## [2.0.0] - 2024-08-02

### Changed
- **BREAKING**: Migrated to Clean Architecture
  - All code now under `yosai_intel_dashboard/src/`
  - Old imports still work via symlinks (deprecated)
  - Symlinks will be removed in next major version
  
### Added
- Clean Architecture structure
- Migration guide (`docs/migration_guide_clean_arch.md`)
- Rollback procedures
- Validation scripts

### Migration Notes
- Update imports: `from models.X` → `from yosai_intel_dashboard.src.core.domain.entities.X`
- Update imports: `from services.X` → `from yosai_intel_dashboard.src.services.X`
- Update imports: `from config.X` → `from yosai_intel_dashboard.src.infrastructure.config.X`
