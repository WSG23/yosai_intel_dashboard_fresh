# UI Accessibility Guidelines

This project aims to meet WCAG 2.1 AA requirements. Follow these rules when developing new components.

## Best Practices

- Prefer semantic HTML elements over generic `<div>`s
- Provide descriptive `aria-label` or `aria-labelledby` attributes for controls
- Maintain a logical tab order and visible focus styles
- Ensure color contrast ratios of at least 4.5:1
- Announce dynamic updates using `aria-live` regions
- Include captions or summaries for data tables
- Associate all form fields with `<label>` elements
- Use `role` attributes when semantics are unclear (e.g. drop zones)
- Mark decorative icons with `aria-hidden="true"`
- Test keyboard navigation and screen reader output regularly

## Accessibility Checklist

- [ ] Interactive elements are reachable via keyboard
- [ ] Buttons use `<button>` elements
- [ ] Images include `alt` text or `aria-hidden`
- [ ] Modals trap focus and use `role="dialog"`
- [ ] Tables use proper headers and captions
- [ ] Progress indicators expose `role="progressbar"`
- [ ] No color is the only means of conveying information
- [ ] ARIA attributes are used correctly and sparingly
