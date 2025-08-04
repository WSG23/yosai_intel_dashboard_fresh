# Analytics Dashboard Methodology

The usage dashboard aggregates in-application events to highlight feature adoption, error frequency, and user proficiency. UI components record activity through `services/analytics/usage.ts`, which maintains counters for adoption and errors while tracking proficiency levels per user. Updates are broadcast on the `usage_update` event channel, allowing `pages/UsageDashboard.tsx` to render live metrics.

This approach provides a lightweight view of engagement without external dependencies. Metrics can be reset or extended with additional event types as new analytics requirements arise.
