# Select

The `Select` component is a styled wrapper around the native `<select>` element. It supports single and multiple selection while remaining accessible and keyboard friendly. The component is generic (`Select<T extends string>`) and exports an `Option<T>` type for strongly typed option values.

## Props

| Prop | Type | Description |
| ---- | ---- | ----------- |
| `value` | `T | T[]` | The current selection. |
| `onChange` | `(value: T | T[]) => void` | Callback fired when the selection changes. |
| `options` | `Option<T>[]` | Available choices. |
| `multiple` | `boolean` | Enables multi-select mode. |
| `placeholder` | `string` | Placeholder text for single select. |
| `className` | `string` | Additional CSS classes. |
| `searchable` | `boolean` | Adds an internal search input to filter options. |
| `...rest` | `SelectHTMLAttributes` | Any other native `<select>` props (e.g. `aria-label`). |

## Searchable Example

```tsx
const fruits = [
  { value: 'apple', label: 'Apple' },
  { value: 'banana', label: 'Banana' },
  { value: 'cherry', label: 'Cherry' },
];

function SearchableSelect() {
  const [value, setValue] = React.useState('');
  return (
    <Select
      aria-label="Fruit"
      options={fruits}
      value={value}
      onChange={setValue}
      placeholder="Pick a fruit"
      searchable
    />
  );
}
```

## Multi-select Example

```tsx
const languages = [
  { value: 'html', label: 'HTML' },
  { value: 'css', label: 'CSS' },
  { value: 'js', label: 'JavaScript' },
];

function LanguagePicker() {
  const [value, setValue] = React.useState<string[]>([]);
  return (
    <Select
      multiple
      aria-label="Languages"
      options={languages}
      value={value}
      onChange={setValue}
    />
  );
}
```

## Keyboard Interaction

The component relies on the native `<select>` element, enabling users to navigate with arrow keys, typeahead search, and `Space` or `Enter` to confirm selection. Custom key handling can be added via the `onKeyDown` prop.

## Design System

Refer to [UI Accessibility](ui_accessibility.md) and [Component Styling](ui_design/component_styling.md) to align with design tokens and interaction patterns.
