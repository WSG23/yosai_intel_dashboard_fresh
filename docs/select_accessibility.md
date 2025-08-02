# Accessible Select Component

The custom `Select` component implements the [combobox](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/) pattern. It exposes a search input linked to a list of options to provide screen‑reader friendly autocomplete behaviour.

## Roles and States

- The search input uses `role="combobox"` and manages `aria-expanded` to reflect whether the option list is visible.
- The option list is rendered as a `role="listbox"` with an `id` referenced by the input's `aria-controls`.
- Each option is rendered with `role="option"`. The currently highlighted option is communicated through `aria-activedescendant` on the combobox.
- When `multiple` is enabled, the listbox exposes `aria-multiselectable="true"`.
- A hidden `role="status"` region announces the number of available results for screen readers.

## Usage

```tsx
<Select
  value={value}
  onChange={setValue}
  options={options}
  multiple
  placeholder="Search…"
/>```

The component filters options as the user types and automatically updates all ARIA attributes to keep assistive technologies informed.

