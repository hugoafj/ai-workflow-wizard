# Protocol: Testing (stack, layers, configs)

<!--
  SINGLE SOURCE of the permanent testing rules and templates. Consumed by phase46
  (configs + extras), the Builder (Testing Approach in AGENTS.md), wf-settings
  (extras). Source in inventory.md: phase46 (all), phase6a 53-55,
  AI_DEV_WORKFLOW 7.4 / 9.x. The concrete artifacts are the *.tmpl.md and *.section.md
  files in this directory (VERBATIM from the source).
-->

## What the testing stack adds

Without testing, `checks_before_done` = `lint + build`. With testing, the done-gate
also verifies that changes do not break behavior (adds `test`, `test:e2e`).

## Testing profiles (state.testing.profile)

The runner, packages, config and file conventions depend on the framework. They live in
`profiles.md` (single source) and are resolved in phase 46. A project that already has a
configured runner keeps it (`state.testing.runner_existing`): nothing is installed or
generated for the unit layer.

| Profile | Frameworks | Runner when the project has none |
|---|---|---|
| `react` | React, Vite | Vitest + Testing Library + jsdom |
| `next` | Next.js | Same as `react`; Playwright targets port 3000 |
| `vue` | Vue, Nuxt | Vitest + Vue Test Utils + jsdom |
| `node-api` | Express, Fastify, Hono, Koa | Vitest (node environment) + supertest |
| `nest` | NestJS | Jest + supertest |
| `angular` | Angular | The project's native runner (no config generated) |
| `laravel` | Laravel | PHPUnit (Pest also accepted), run with `php artisan test`; installed with Composer, no config generated |
| `php` | Any other PHP project | PHPUnit, run with `vendor/bin/phpunit`; installed with Composer, no config generated |
| `generic` | Anything else | Chosen in phase 46 (Vitest in node environment, or none) |

## The three layers (user selection → state.testing.layers)

1. **Unit** — the profile's runner. Tests functions, services and components in isolation.
   The file convention and the generated config come from the profile. Vitest profiles add
   the scripts `test`, `test:ui`, `test:coverage`; Nest keeps Jest's `test`, `test:watch`.
2. **Integration** — same runner as unit. The convention comes from the profile
   (render tests for UI stacks, supertest for API stacks). Requires layer 1.
3. **E2E** — Playwright (Chromium by default). Generates `playwright.config.ts`, `e2e/`.
4. **Frontend** (a PHP project whose `discovery.stack.frontend` is not `none`) — the unit tests of its UI with the
   JS profile of that framework (React: Vitest + Testing Library; Vue: Vitest + Vue Test Utils). Generates a
   `vitest.config.ts` that only runs tests under the frontend folder and `tests/js/` and, for React, treats the
   `.js` files there as JSX; `tests/js/setup.ts`; an example test when the frontend has none. Independent of
   layer 1: the PHP runner being kept never keeps the frontend's, and the other way round. Recorded as
   `frontend` in `state.testing.layers`.
   Scripts: `test:e2e`, `test:e2e:ui`, `test:e2e:report`. Activates the Playwright MCP.
   API profiles (`"e2e": "off"` in `profiles.md`) do not offer it in phase 46.

> The exact layer menu is asked in phase46 and stored in `state.testing`. The
> coverage-by-change-type matrix, the Playwright dual loop and the headed-run output
> rule are in `testing-approach.section.md`.

## Optional extras (state.testing: coverage_threshold, visual_regression, page_object_model)

- **coverage**: configurable threshold → `coverage-thresholds.tmpl.md` in `vitest.config.ts`
  (`coverage-thresholds.jest.tmpl.md` in `jest.config.js` for the Nest profile).
- **visual regression**: Playwright snapshots → `visual-snapshots.tmpl.md`.
- **POM**: generates `e2e/pages/` and updates the convention in AGENTS.md.

## Artifact templates (VERBATIM in this directory)

| Target file | Template |
|---|---|
| Unit config (by profile) | `vitest.config.tmpl.md` (react), `vitest.vue.config.tmpl.md` (vue), `vitest.node.config.tmpl.md` (node-api, generic), `jest.config.nest.tmpl.md` (nest), plus `coverage-thresholds.tmpl.md` / `coverage-thresholds.jest.tmpl.md` if coverage |
| `src/test/setup.ts` | `setup.tmpl.md` (react profile) |
| Profile data (runner, packages, scripts, conventions) | `profiles.md` |
| `playwright.config.ts` | `playwright.config.tmpl.md` |
| `e2e/example.spec.ts` | `e2e-example.tmpl.md` |
| package.json scripts | `test-scripts.tmpl.md`, `e2e-scripts.tmpl.md` |
| Playwright MCP settings | `playwright-mcp.settings.tmpl.md` |
| AGENTS.md `## Testing Approach` | `testing-approach.section.md` (`testing-approach.backend.section.md` matrix for API profiles) |
| AGENTS.md E2E convention | `data-testid.section.md` (UI profiles only) |
| AGENTS.md checks | `checks.section.md` |

## data-testid convention (E2E) — mandatory if layer 3 on a UI profile

See `data-testid.section.md` (VERBATIM). The Builder appends it only when the profile has
`"ui": true`; API profiles have no markup to annotate. `npx @playwright/mcp` does not require an API key
(committable). Install browsers: `npx playwright install --with-deps chromium`.
