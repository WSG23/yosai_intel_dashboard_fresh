# ErrorBoundary

The `ErrorBoundary` component wraps part of the React tree and renders a fallback UI when a child throws an error. It prevents entire pages from crashing and logs diagnostic information.

## Props

| Prop | Type | Description |
| ---- | ---- | ----------- |
| `children` | `ReactNode` | Content to be protected by the boundary. |

## Basic Usage

```tsx
<ErrorBoundary>
  <DangerousWidget />
</ErrorBoundary>
```

## Retry Example

Use a changing `key` to reset the boundary after an error.

```tsx
function ExplodingComponent({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Kaboom');
  }
  return <div>All good</div>;
}

export function RetryExample() {
  const [key, setKey] = React.useState(0);
  const [throwErr, setThrowErr] = React.useState(false);
  return (
    <ErrorBoundary key={key}>
      <ExplodingComponent shouldThrow={throwErr} />
      <button onClick={() => setThrowErr(true)}>Trigger Error</button>
      <button onClick={() => setKey(k => k + 1)}>Retry</button>
    </ErrorBoundary>
  );
}
```

## Design System

Follow the guidance in [UI Accessibility](ui_accessibility.md) and [UI Design](ui_design/README.md) for consistent error messaging and focus handling.
