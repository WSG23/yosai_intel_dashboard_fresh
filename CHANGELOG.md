# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial changelog with standard sections.

### Changed
- Updated `run_service_analysis` to use `analyze_data_with_service` and
  `create_analysis_results_display`.

### Fixed
- Navigation bar icons failed to load when `app.get_asset_url` returned
  `None`. Asset utilities now fall back to direct `/assets/` paths.
- Removed unused "Use Camera" button from the file upload component.
- Reduced `.nav-icon` size to `2rem` for better appearance with fallback
  Font Awesome icons.

