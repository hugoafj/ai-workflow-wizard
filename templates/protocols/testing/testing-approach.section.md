<!--
  REFERENCE ONLY — the resolved Testing Approach section in generated AGENTS.md is
  produced deterministically by wf-init/lib/builder-core.py (testing_approach_section())
  from state.testing.layers. Do NOT inline this file as an instruction text; it exists
  here as documentation of the canonical section the builder generates.
-->

## Testing Approach

### Unit & Integration

Run the unit/integration suite before considering a change done:

```bash
npm run test
```

- Unit: Vitest + Testing Library. File: `Component.test.tsx` next to the component.
- Integration: Vitest + Testing Library with real render. File: `*.integration.test.tsx` in `src/__tests__/integration/`.

### E2E

Run the end-to-end suite (specs by flow) before merge:

```bash
npm run test:e2e
```

- E2E: Playwright (Chromium). Specs in `e2e/<feature-name>.spec.ts`.
  One file per user flow, named by the flow — not by the component or hook.
  Examples: `persistence.spec.ts`, `task-creation.spec.ts`, `categories.spec.ts`.