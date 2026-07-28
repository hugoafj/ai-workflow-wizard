**Update the Testing section of `AGENTS.md`** — look for the `## Testing` (or `## Testing Approach`) section and replace it with:

```markdown
## Testing Approach

<based on active layers — include only the active ones>
- Unit: Vitest + Testing Library. `npm run test`. File: `Component.test.tsx` next to the component.
- Integration: Vitest + Testing Library with real render. `npm run test`. File: `*.integration.test.tsx` in `src/__tests__/integration/`.
- E2E: Playwright (Chromium). `npm run test:e2e`. Specs in `e2e/<feature-name>.spec.ts`.
  One file per user flow, named by the flow — not by the component or hook.
  Examples: `persistence.spec.ts`, `task-creation.spec.ts`, `categories.spec.ts`.
