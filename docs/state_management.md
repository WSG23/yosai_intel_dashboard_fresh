# State Management

The initial React frontend used a global Zustand store to replace the legacy
Dash `dcc.Store` components. After evaluating our state needs we migrated to
**Redux Toolkit**. Redux offers a richer ecosystem, built‑in dev tools and easy
middleware integration, which simplifies features like undo/redo and time travel
debugging.

Current slices:

- **session** – data scoped to the active user session
- **analytics** – cached analytics responses by key
- **upload** – tracking files queued for upload
- **selection** – page level selections such as highlighted threats
- **history** – generic undo/redo stack shared across features

All slices live under `src/adapters/ui/state` and are combined in
`state/store.ts`. Use the exported `useAppDispatch` and `useAppSelector` hooks
from the same module when reading or updating state.
