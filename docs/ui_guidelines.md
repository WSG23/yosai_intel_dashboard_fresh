# UI Guidelines

## Progressive Reveal

Use the `ProgressiveSection` component to hide complex metrics or settings until users request them. This pattern keeps interfaces focused while maintaining accessibility. It should wrap drill‑down metrics and advanced settings that are not necessary for an initial scan of the page.

```tsx
<ProgressiveSection title="Advanced Settings">
  {/* advanced controls here */}
</ProgressiveSection>
```

Content wrapped in `ProgressiveSection` is hidden from screen readers and keyboard navigation until expanded, reducing noise for assistive technology users. Toggle buttons manage `aria-expanded`, while the content container uses `aria-hidden` and the `hidden` attribute.
