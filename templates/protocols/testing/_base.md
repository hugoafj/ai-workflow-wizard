# Protocol: Testing (stack, layers, configs)

<!--
  SINGLE SOURCE of the permanent testing rules and templates. Consumed by phase46,
  phase46b (configs + extras), the Builder (Testing Approach in AGENTS.md), wf-settings
  (extras). Source in inventory.md: phase46 1-5, phase46b (all), phase6a 53-55,
  AI_DEV_WORKFLOW 7.4 / 9.x. The concrete artifacts are the *.tmpl.md and *.section.md
  files in this directory (VERBATIM from the source).
-->

## What the testing stack adds

Without testing, `checks_before_done` = `lint + build`. With testing, the SDD pipeline
automatically verifies that changes do not break behavior (adds `test`,
`test:e2e`).

## The three layers (user selection → state.testing.layers)

1. **Unit** — Vitest + Testing Library. Tests functions/hooks/utilities in isolation.
   Convention: `Component.test.tsx` next to the file. Generates `vitest.config.ts`,
   `src/test/setup.ts`. Scripts: `test`, `test:ui`, `test:coverage`.
2. **Integration** — same runner as unit. Convention: `*.integration.test.tsx` in
   `src/__tests__/integration/`. Requires layer 1.
3. **E2E** — Playwright (Chromium by default). Generates `playwright.config.ts`, `e2e/`.
   Scripts: `test:e2e`, `test:e2e:ui`, `test:e2e:report`. Activates the Playwright MCP.

> The exact layer menu and TDD mode (standard/strict) are asked in phase46 and
> stored in `state.testing`. The TDD Protocol itself lives in the `tdd` protocol.

## Optional extras (state.testing: coverage_threshold, visual_regression, page_object_model)

- **coverage**: configurable threshold → `coverage-thresholds.tmpl.md` in `vitest.config.ts`.
- **visual regression**: Playwright snapshots → `visual-snapshots.tmpl.md`.
- **POM**: generates `e2e/pages/` and updates the convention in AGENTS.md.

## Artifact templates (VERBATIM in this directory)

| Target file | Template |
|---|---|
| `vitest.config.ts` | `vitest.config.tmpl.md` (+ `coverage-thresholds.tmpl.md` if coverage) |
| `src/test/setup.ts` | `setup.tmpl.md` |
| `playwright.config.ts` | `playwright.config.tmpl.md` |
| `e2e/example.spec.ts` | `e2e-example.tmpl.md` |
| package.json scripts | `test-scripts.tmpl.md`, `e2e-scripts.tmpl.md` |
| Playwright MCP settings | `playwright-mcp.settings.tmpl.md` |
| AGENTS.md `## Testing Approach` | `testing-approach.section.md` |
| AGENTS.md E2E convention | `data-testid.section.md` |
| AGENTS.md checks | `checks.section.md` |

## data-testid convention (E2E) — mandatory if layer 3

See `data-testid.section.md` (VERBATIM). `npx @playwright/mcp` does not require an API key
(committable). Install browsers: `npx playwright install --with-deps chromium`.
