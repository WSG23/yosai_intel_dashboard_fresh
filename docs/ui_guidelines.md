# UI Guidelines

## Progressive Reveal

Use the `ProgressiveSection` component to hide complex metrics or settings until users request them. This pattern keeps interfaces focused while maintaining accessibility. It should wrap drill‑down metrics and advanced settings that are not necessary for an initial scan of the page.

```tsx
<ProgressiveSection title="Advanced Settings">
  {/* advanced controls here */}
</ProgressiveSection>
```

Content wrapped in `ProgressiveSection` is hidden from screen readers and keyboard navigation until expanded, reducing noise for assistive technology users. Toggle buttons manage `aria-expanded`, while the content container uses `aria-hidden` and the `hidden` attribute.

## Responsive Design and Dark Mode

- The dashboard uses Tailwind CSS with a mobile-first approach. Apply responsive utility classes such as `sm:`, `md:`, and `lg:` to ensure components scale from phones to desktops.
- The navigation bar collapses into a menu on small screens. Dark mode is controlled by the `useDarkMode` hook, which toggles a `dark` class on the root element. Use Tailwind's `dark:` variant to style components for both themes.

### Testing

Run `npm test` in the project root to execute responsive layout tests and verify dark mode behavior.
