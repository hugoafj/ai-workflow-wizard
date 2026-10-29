<!--
  SOURCE of the guidance appended to the generated Testing Approach section.
  wf-init/lib/builder-core.py (testing_approach_section()) builds the layer commands and
  file conventions from state.testing.layers, then appends the coverage matrix (when unit,
  integration or e2e is active) and the E2E guidance (when e2e is active) from this file.
  The text after the "### Playwright dual loop" heading is emitted only for e2e projects.
  Do not add the "## Testing Approach" heading or the command blocks here.
-->

### Coverage by change type

| Change type | Unit | Integration | E2E |
|---|---|---|---|
| Logic in a hook or `lib/` | Yes | No | No |
| Component with its own state | Yes | Optional | No |
| Multi-component flow | No | Yes | No |
| Complete user feature | No | Yes | Yes |
| Bug fix with possible regression | Based on origin | No | No |
| Pure UI or styles | No | No | No |

This matrix is a guideline. If logic could break silently and the table does not
cover it, add tests anyway.

### Playwright dual loop

Before writing a new E2E spec, decide whether the flow needs visual exploration first.

Explore first with the Playwright MCP when the flow has several visual states or
transitions (loading, error, success, animations, layout changes), when the interaction
has never been tested before, or when the user asks for visual validation before
committing to the spec.

Go straight to the spec for simple, well-known CRUD flows (create, edit, delete) without
complex visual states, or when a similar spec already exists to use as a template.

When you explore first, navigate, interact and capture screenshots of the real flow on
the dev server without writing files. Once the flow behaves as expected, write the
versioned spec in `e2e/` and follow the Red-Green-Refactor cycle.

### Headed run for new E2E specs

Whenever E2E specs were generated, show the user the command to watch them run in the
browser before declaring the task done or committing. Use the exact path of the new spec,
never a generic command:

```bash
npm run test:e2e -- --headed --workers=1 --project=chromium e2e/<exact-name>.spec.ts
```

This output is mandatory whenever E2E specs were generated, because it is easy to skip
while moving toward the commit.
