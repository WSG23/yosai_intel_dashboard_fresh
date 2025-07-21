# Project Roadmap

This roadmap outlines the major milestones planned for the Yōsai Intel Dashboard.

## Milestones

### Q1: Core Platform

- Implement user authentication and session management
  - Login and registration pages with token-based sessions
  - Role-based permission system for API routes
  - Secure session store with periodic expiration
  - Initial CI pipeline and containerized development workflow

### Q2: File Ingestion Improvements

- Improve file ingestion pipeline with stronger validation
  - Checksum verification and progress tracking for uploads
  - Graceful error reporting for misformatted files
  - Built-in validators for common log and image formats
  - Instrumentation metrics for ingestion performance

### Q3: Advanced Analytics

- Add advanced analytics generation and reporting features
  - Event correlation across facilities and interactive time-series graphs
  - Pluggable anomaly detection models
  - Scheduled reporting with CSV and PDF export options
  - Data versioning support for reproducible analysis

### Q4: Ecosystem Expansion

- Launch plugin marketplace and developer SDK
  - Public registry for community plugins
  - CLI tools for scaffolding new plugins
  - Comprehensive documentation with code samples
  - Zero-downtime deployment procedures for upgrades

The timeline may adjust as priorities evolve, but these phases capture the
current goals for the upcoming releases.
