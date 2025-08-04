# UI Guidelines

## Progressive Reveal

Use the `ProgressiveSection` component to hide complex metrics or settings until users request them. This pattern keeps interfaces focused while maintaining accessibility.

```tsx
<ProgressiveSection title="Advanced Settings">
  {/* advanced controls here */}
</ProgressiveSection>
```

Content wrapped in `ProgressiveSection` is hidden from screen readers and keyboard navigation until expanded, reducing noise for assistive technology users.
