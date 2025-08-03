# Accessibility Audit

A quarterly review was performed against WCAG 2.1 AA guidelines.

## Findings

- Navigation and forms expose appropriate ARIA labels.
- Keyboard focus is visible on all interactive elements.
- Contrast ratios meet the 4.5:1 threshold.
- Remaining issue: tables lack captions in several reports.

## Mobile Optimization Notes

- Layouts respond to narrow viewports using CSS grid.
- Touch targets are at least 44 px by 44 px.
- Charts collapse into scrollable containers on small screens.
- Avoid hover‑only interactions; provide tap equivalents.
