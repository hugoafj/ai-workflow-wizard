<if e2e layer active (layer 3)>:
### `data-testid` convention (mandatory on interactive components)

Every element that an E2E test interacts with (buttons, inputs, links,
clickable elements) MUST have its own `data-testid` attribute, added
by the agent when creating the component — not added afterwards, retroactively,
only when a test needs it.

Format: `data-testid="<context>-<element>"`, in kebab-case, specific
without being redundant. Examples: `data-testid="task-item-delete-button"`,
`data-testid="category-filter-select"`.

Why: without this, E2E specs look for elements by visible text or
Tailwind classes — both change frequently during normal development and
break tests unrelated to the actual change. `data-testid` is
stable against style or copy refactors.

Do not confuse with internal `data-*` attributes from third-party libraries
(e.g., `data-radix-scroll-area-viewport` from Radix UI) — those are internal
library mechanisms, not the project's testing convention.
