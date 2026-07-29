## PHASE 4.6 (continued) — Optional extras, configs and MCP registration — conditional

> **Gate**: only runs if `features.tdd_protocol == true`. If phase46 was executed, this phase also applies.

```bash
FEATURES_TDD=$(jq -r '.features.tdd_protocol // false' .wizard-state.json)
if [ "$FEATURES_TDD" != "true" ]; then
  echo "PHASE 4.6b skipped — TDD Protocol not selected."
  NEXT=
  if [ "$(jq -r '.features.ci // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.cd // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.release_please // false' .wizard-state.json)" = "true" ]; then
    NEXT="phase47-cicd"
  else
    NEXT="phase5"
  fi
  wf_phase_done phase46b "$NEXT"
  exit 0
fi
```

### Optional testing extras (always asked, never activated by default)

Regardless of the chosen TDD mode, ask if the user wants to
activate any of these extras. They are optional because they have a real cost
(maintenance, execution tokens, or risk of over-engineering in a
small project) that isn't justified in every case — the Decision
Ladder of this same wizard exists precisely to avoid activating things the
project doesn't need yet.

```
Optional testing extras — none are activated unless you ask:

────────────────────────────────────────────────────────────
1. Configurable coverage targets

   Define a minimum code coverage percentage. If the project
   drops below it, `npm run test -- --coverage` fails locally
   (and in CI, when the Block 6 pipeline exists). Cost: nearly zero
   — it's one config line in vitest.config.ts.

2. Visual regression (Playwright snapshots)

   Compares screenshots against a saved reference and fails
   if something visual changed without approval. Real cost: each run takes
   longer (renders and compares images), and references have to be
   re-generated manually every time you intentionally change the design —
   ongoing maintenance, not just initial setup.

3. Page Object Model (POM) for E2E

   Organizes Playwright selectors into reusable classes instead
   of repeating them in every spec. No execution cost, but it's a layer
   of abstraction that's only worthwhile with several E2E specs — in a
   project with 2-3 flows, it's over-engineering.
────────────────────────────────────────────────────────────

Which ones do I activate? [comma-separated numbers / none for now]
```

**Wait for user response.**

**If they activated extra 1 (coverage targets)**, ask for the threshold and add the
`coverage.thresholds` block to `vitest.config.ts`:

```
What minimum coverage percentage do you want to require? (recommended: 70-80%
for projects in active development, 100% only if you have critical
utility libs that warrant it)

[70 / 80 / 90 / other: specify]
```

```typescript
// Add inside test: { ... } in vitest.config.ts
coverage: {
  provider: 'v8',
  thresholds: {
    lines: <umbral>,
    functions: <umbral>,
    branches: <umbral>,
    statements: <umbral>,
  },
},
```

**If they activated extra 2 (visual regression)**, add to `playwright.config.ts`
the snapshot configuration and generate an example spec:

```typescript
// Add inside defineConfig({ ... })
expect: {
  toHaveScreenshot: { maxDiffPixels: 100 },
},
```

Inform the user that references are generated the first time they run
`npx playwright test --update-snapshots`, and that they must review and commit
those reference images manually.

**If they activated extra 3 (POM)**, generate an `e2e/pages/` folder with a minimal
example (one class per page already covered by the existing example spec),
and update the convention in the Testing Approach section of AGENTS.md so
the agent follows it in future specs.

**If they activated layer 1 or 1+2 (Vitest)**:

`vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    exclude: ['**/node_modules/**', '**/e2e/**'],
  },
})
```

> **Why the `exclude`**: without it, Vitest picks up Playwright specs in `e2e/` and fails with "Playwright Test did not expect test() to be called here". This happens in any project that activates unit + e2e together.

`src/test/setup.ts`:
```typescript
import '@testing-library/jest-dom'
```

Scripts to add to `package.json`:
```json
"test": "vitest",
"test:ui": "vitest --ui",
"test:coverage": "vitest run --coverage"
```

**If they activated layer 3 (Playwright)**:

`playwright.config.ts`:
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
})
```

`e2e/example.spec.ts`:
```typescript
import { test, expect } from '@playwright/test'

test('app loads correctly', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/.*/)
})
```

Scripts to add:
```json
"test:e2e": "playwright test",
"test:e2e:ui": "playwright test --ui",
"test:e2e:report": "playwright show-report"
```

### Additional MCPs by stack

Detect additional MCPs based on the project's actual stack:

```bash
# Detect dependencies that imply specific MCPs
cat package.json | grep -E '"@supabase|"pg|"postgres|"stripe|"github|"octokit' 2>/dev/null
# Detect .env.example files with API keys that reveal services
cat .env.example 2>/dev/null || cat .env.local.example 2>/dev/null
```

Based on what's detected, ask the user which additional MCPs to activate:

```
Detected the following dependencies that could benefit from MCPs:

<list of detected MCPs based on package.json, one per line with description>

Which ones would you like to configure? [comma-separated numbers / none]

Note: Engram and Context7 are already active via gentle-ai — they don't need configuration.
```

For each selected additional MCP, register it in the MCPs table of AGENTS.md
(generated in Phase 6) with its purpose and the required setup type.
MCPs that require credentials are marked as "API key in `.env.local`" —
wf-onboard will guide the new developer through that step.

**Concrete instructions for Phase 8** (what the wizard explicitly writes, with instructions on how) — edit `openspec/config.yaml` with the actual values:

```bash
# Read current config
cat openspec/config.yaml
```

Generate the updated version in memory with these fields modified according to the activated layers:

```yaml
testing:
  strict_tdd: false        # true if they chose option 2 — REAL FIELD, it's the source
                            # that gentle-ai's sdd-apply queries directly
                            # (confirmed against the actual installed skill source)
  configured: true
  runner: vitest          # or "playwright" if only e2e, or "vitest+playwright" if both
  planned: null           # no longer "planned", it's configured
layers:
  unit: true              # if layer 1 was activated
  integration: true       # if layer 2 was activated
  e2e: true               # if layer 3 was activated
  coverage: false         # true if extra 1 was activated (coverage targets)
extras:
  coverage_threshold: null      # number if extra 1 was activated, e.g. 80
  visual_regression: false      # true if extra 2 was activated
  page_object_model: false      # true if extra 3 was activated
conventions:
  unit: "Component.test.tsx — junto al componente"
  integration: "*.integration.test.tsx — en src/__tests__/integration/"
  e2e: "e2e/<feature-name>.spec.ts — one file per user flow, named by flow not by component"
checks_before_done:
  - npm run lint
  - npm run build
  - npm run test          # add if unit/integration was activated
  - npm run test:e2e      # add if e2e was activated
```

Write the complete `openspec/config.yaml` with those values (not just the changed fields — rewrite the entire file to avoid malformed YAML).

**Update the Testing section of `AGENTS.md`** — find the `## Testing` (or `## Testing Approach`) section and replace it with:

```markdown
## Testing Approach

<based on activated layers — include only active ones>
- Unit: Vitest + Testing Library. `npm run test`. File: `Component.test.tsx` next to the component.
- Integration: Vitest + Testing Library with real render. `npm run test`. File: `*.integration.test.tsx` in `src/__tests__/integration/`.
- E2E: Playwright (Chromium). `npm run test:e2e`. Specs in `e2e/<feature-name>.spec.ts`.
  One file per user flow, named by the flow — not by the component or hook.
  Examples: `persistence.spec.ts`, `task-creation.spec.ts`, `categories.spec.ts`.

<if layer 3 (e2e) activated>:
### `data-testid` Convention (mandatory on interactive components)

Every element that an E2E test interacts with (buttons, inputs, links,
clickable elements) MUST have its own `data-testid` attribute, added
by the agent when creating the component — not added later, a posteriori,
only when a test needs it.

Format: `data-testid="<context>-<element>"`, in kebab-case, specific
without being redundant. Examples: `data-testid="task-item-delete-button"`,
`data-testid="category-filter-select"`.

Why: without this, E2E specs look for elements by visible text or
Tailwind classes — both change frequently during normal development and
break tests unrelated to the actual change. `data-testid` is
stable against style or copy refactors.

Don't confuse with internal `data-*` attributes of third-party libraries
(e.g. `data-radix-scroll-area-viewport` from Radix UI) — those are internal
library mechanisms, not the project's testing convention.

Before declaring a task done, the agent MUST run and leave green:
\`\`\`bash
npm run lint
npm run build
npm run test        # if unit/integration
npm run test -- --coverage  # if coverage targets activated — must meet the configured threshold
npm run test:e2e    # if e2e
\`\`\`
```

**Register Playwright MCP** (only if the user activated layer 3) — add the MCP to the active agent's configuration. The Playwright MCP is `@playwright/mcp` and lets the agent launch browsers during sdd-apply and sdd-verify.

For Claude Code, the MCP is registered in `.claude/settings.json` (or `.claude/settings.local.json` to avoid committing it if it has an API key):

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp"]
    }
  }
}
```

For other agents configured in this project, check each one's MCP registration format (Cursor: `.cursor/mcp.json`, Windsurf: `.windsurf/mcp.json`). If the format isn't clear for any agent, tell the user which files to create and with what content, and wait for confirmation before writing.

> **Note**: `npx @playwright/mcp` doesn't require an API key — it launches Playwright directly. There are no credentials to protect. It IS reasonable to commit this MCP to the repo so all developers on the team have it.

**Install Playwright browsers** (after `npm install`):

```bash
npx playwright install --with-deps chromium
```

This command downloads the browser. It only needs to be run once per machine. If the user is on CI, the CI workflow also needs this command.

### ✓ PHASE 4.6 COMPLETED

```
Testing stack configured (in memory — everything is written in Phase 8):

  TDD Mode: <Standard TDD Protocol / Strict TDD Mode>

  New files:
    <if unit>  vitest.config.ts ✓  (with exclude: e2e/)
    <if unit>  src/test/setup.ts ✓
    <if e2e>   playwright.config.ts ✓
    <if e2e>   e2e/example.spec.ts ✓
    <if POM>   e2e/pages/ ✓ (minimal example)

  Files modified in Phase 8:
    package.json  → test scripts added
    AGENTS.md     → Testing section updated + TDD Protocol (automatically included)
    openspec/config.yaml → testing.configured: true, layers, extras, checks_before_done

  Playwright MCP:
    <if e2e>  .claude/settings.json (and IDE equivalents) ← Phase 8

  Activated extras:
    <if coverage>          - Minimum coverage: <threshold>%
    <if visual regression> - Visual regression (snapshots) active
    <if POM>                - Page Object Model active

  Final checks_before_done:
    - npm run lint
    - npm run build
    <if unit>      - npm run test
    <if coverage>  - npm run test -- --coverage
    <if e2e>       - npm run test:e2e
```

> TDD Protocol (or Strict TDD Mode, depending on choice) is automatically included
> in AGENTS.md when testing is configured — there's no additional question
> in Phase 0c (feature selection), it was already asked here in Phase 4.6. It's the documentation of the
> behavior that the testing stack enables.

**PAUSE — Wait for "continue" or "yes" to move to the next phase (based on features chosen in Phase 0c).**

---
> **⛔ STOP HERE — don't execute anything else.**
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `testing.extras` (coverage/visual/POM), `testing.coverage_threshold` (if applicable), `mcps` (project MCPs to configure). Mark `wf_phase_done phase46b <next>`.
> Calculate the next phase based on features:
> ```bash
> if jq -e '.features.ci == true or .features.cd == true or .features.release_please == true' .wizard-state.json >/dev/null; then
>   echo "phase47-cicd"
> else
>   echo "phase5"
> fi
> ```
> Tell the user: *"Testing stack configured. Reply **continue** to continue."*
> Wait for the response. Only when they confirm, execute in bash: `cat "$WF_DIR/$NEXT.md"`
