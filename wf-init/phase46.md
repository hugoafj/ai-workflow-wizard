## PHASE 4.6: Testing stack setup (conditional)

> **Gate**: only runs if `features.testing == true`. This phase covers the test layers, the wiring check, the test infrastructure and the optional testing extras (coverage threshold, visual regression, POM).

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

FEATURES_TESTING=$(jq -r '.features.testing // false' .wizard-state.json)
if [ "$FEATURES_TESTING" != "true" ]; then
  echo "PHASE 4.6 skipped: testing not selected."
  NEXT=
  if [ "$(jq -r '.features.ci // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.cd // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.release_please // false' .wizard-state.json)" = "true" ]; then
    NEXT="phase47-cicd"
  else
    NEXT="phase5"
  fi
  wf_phase_done phase46 "$NEXT"
  echo "ℹ Next phase: $NEXT"
  cat "$WF_DIR/$NEXT.md"
  exit 0
fi
```

The testing stack lets the pipeline verify each change automatically. Without this phase, the checks before done only cover lint and build. With it, they add `test`, `test:e2e`, or both, depending on the layers you activate.

This phase is optional but highly recommended. If the user prefers to configure it later, they can run `/wf-onboard` when they install a test runner.

First detect if there's already a test runner configured:

```bash
grep -E '"(@(playwright/test|testing-library/|vitest/)|vitest|jest|cypress|playwright)"' package.json 2>/dev/null
ls vitest.config.ts vitest.config.js jest.config.ts playwright.config.ts 2>/dev/null
```

**If a test runner already exists**: report what was found and ask if they want to add missing
layers. Don't install anything without confirmation.

**Check wiring, not just dependencies** (field report B8): a dependency without its config is a
BROKEN layer, not a configured one. A project with `@playwright/test` installed but no
`playwright.config.ts` crashes on its first e2e run (`npx playwright test --list` picks up unit
specs). So for each layer report BOTH signals and only declare it configured when both are
present:

- Unit/integration: vitest/jest dependency AND `vitest.config.*`/`jest.config.*` (or a `test:` block in vite config).
- E2E: playwright dependency AND `playwright.config.ts`.

When the dependency exists but the config is missing, treat that layer as NOT configured and
offer to generate the missing config with the wizard's own templates. Optionally smoke-check
e2e wiring before declaring it done: `npx playwright test --list` should list specs without
crashing.

**If there's no test runner**, ask what layers to activate:

### [USER MESSAGE]
```
No configured testing framework detected.

Without tests, the checks only run lint + build. With tests, the pipeline
automatically verifies that changes don't break existing behavior.

What testing layers would you like to configure now?

────────────────────────────────────────────────────────────
1. Unit tests: Vitest + Testing Library

   WHAT IT DOES: tests functions, hooks, and utilities in isolation.
   INSTALLS: vitest, @testing-library/react, @testing-library/user-event,
             @testing-library/jest-dom, jsdom, @vitest/ui, @vitest/coverage-v8
   GENERATES: vitest.config.ts, src/test/setup.ts
   ADDS SCRIPTS: "test", "test:ui", "test:coverage"
   CONVENTION: Component.test.tsx next to the tested file.

2. Integration tests: same stack as unit

   WHAT IT DOES: tests components with real dependencies in jsdom.
   Doesn't require a separate install: uses the layer 1 runner.
   CONVENTION: *.integration.test.tsx in src/__tests__/integration/
   Requires layer 1 to be activated.

3. E2E tests: Playwright

   WHAT IT DOES: complete flows in a real browser (Chromium by default).
   INSTALLS: @playwright/test + browsers via npx playwright install
   GENERATES: playwright.config.ts, e2e/ folder with example spec
   ADDS SCRIPTS: "test:e2e", "test:e2e:ui", "test:e2e:report"
   ENABLES: Playwright MCP so the agent controls the browser during
           implementation and verification.

────────────────────────────────────────────────────────────

What do I activate? [1 / 2 / 1,2 / 1,2,3 / 3 only / none for now]
```

### ⏸ PAUSE: Waiting for user response...

### Optional testing extras (always asked, never activated by default)

Regardless of the layers chosen above, ask if the user wants to
activate any of these extras. They are optional because they have a real cost
(maintenance, execution tokens, or risk of over-engineering in a
small project) that isn't justified in every case. The Decision
Ladder of this same wizard exists precisely to avoid activating things the
project doesn't need yet.

```
Optional testing extras. None are activated unless you ask:

────────────────────────────────────────────────────────────
1. Configurable coverage targets

   Define a minimum code coverage percentage. If the project
   drops below it, `npm run test -- --coverage` fails locally
   (and in CI, when the Block 6 pipeline exists). Cost: nearly zero.
   It's one config line in vitest.config.ts.

2. Visual regression (Playwright snapshots)

   Compares screenshots against a saved reference and fails
   if something visual changed without approval. Real cost: each run takes
   longer (renders and compares images), and references have to be
   re-generated manually every time you intentionally change the design.
   Ongoing maintenance, not just initial setup.

3. Page Object Model (POM) for E2E

   Organizes Playwright selectors into reusable classes instead
   of repeating them in every spec. No execution cost, but it's a layer
   of abstraction that's only worthwhile with several E2E specs. In a
   project with 2-3 flows, it's over-engineering.
────────────────────────────────────────────────────────────

Which ones do I activate? [comma-separated numbers / none for now]
```

### ⏸ PAUSE: Waiting for user response...

**If they activated extra 1 (coverage targets)**, ask for the threshold. It is stored in
`state.testing.coverage_threshold` (persistence below); the builder injects the
`coverage.thresholds` block into `vitest.config.ts` in Phase 6b (step B8, from
`coverage-thresholds.tmpl.md` resolving `{{threshold}}`) and Phase 8 promotes it to the real file;
do NOT edit `vitest.config.ts` here, the file doesn't exist yet in this phase:

```
What minimum coverage percentage do you want to require? (recommended: 70-80%
for projects in active development, 100% only if you have critical
utility libs that warrant it)

[70 / 80 / 90 / other: specify]
```

**If they activated extra 2 (visual regression)**, save `testing.visual_regression: true` in
state (persistence below). The builder injects the snapshot configuration into
`playwright.config.ts` in Phase 6b (step B8, from `visual-snapshots.tmpl.md`) and Phase 8 promotes
it to the real file; do NOT edit `playwright.config.ts` here, the file doesn't exist yet in this phase:

```typescript
// Injected by the builder (visual-snapshots.tmpl.md) inside defineConfig({ ... })
expect: {
  toHaveScreenshot: { maxDiffPixels: 100 },
},
```

Inform the user that references are generated the first time they run
`npx playwright test --update-snapshots`, and that they must review and commit
those reference images manually.

**If they activated extra 3 (POM)**: the Builder stages a minimal scaffold:
`e2e/pages/HomePage.ts` (Phase 6b, from `pom-example.tmpl.md`), and the AGENTS.md Testing
Approach section gains the page-object convention line automatically. It is deliberately a
PATTERN, not real pages: real Page Objects emerge with features as they are built, replacing the
example locators with actual `data-testid` values grepped from components. Nothing is edited
by hand here.

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

Scripts added to `package.json` in Phase 8, step 8.1e (same content as `test-scripts.tmpl.md`):
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

Scripts added to `package.json` in Phase 8, step 8.1e (same content as `e2e-scripts.tmpl.md`):
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

Note: Engram and Context7 are already active via gentle-ai. They don't need configuration.
```

For each selected additional MCP, register it in the MCPs table of AGENTS.md
(generated in Phase 6) with its purpose and the required setup type.
MCPs that require credentials are marked as "API key in `.env.local`". wf-onboard will guide the new developer through that step.

**Testing state**: the testing configuration reaches the agent through the Testing Approach
section of AGENTS.md (below). `visual_regression` and `page_object_model` stay in
`.wizard-state.json` only; they surface in the generated `playwright.config.ts` and `e2e/pages/`.
The wizard writes no other testing configuration file.

**Update the Testing section of `AGENTS.md`**: find the `## Testing` (or `## Testing Approach`) section and replace it with:

```markdown
## Testing Approach

<based on activated layers: include only active ones>
- Unit: Vitest + Testing Library. `npm run test`. File: `Component.test.tsx` next to the component.
- Integration: Vitest + Testing Library with real render. `npm run test`. File: `*.integration.test.tsx` in `src/__tests__/integration/`.
- E2E: Playwright (Chromium). `npm run test:e2e`. Specs in `e2e/<feature-name>.spec.ts`.
  One file per user flow, named by the flow, not by the component or hook.
  Examples: `persistence.spec.ts`, `task-creation.spec.ts`, `categories.spec.ts`.

<if layer 3 (e2e) activated>:
### `data-testid` Convention (mandatory on interactive components)

Every element that an E2E test interacts with (buttons, inputs, links,
clickable elements) MUST have its own `data-testid` attribute, added
by the agent when creating the component, not added later, a posteriori,
only when a test needs it.

Format: `data-testid="<context>-<element>"`, in kebab-case, specific
without being redundant. Examples: `data-testid="task-item-delete-button"`,
`data-testid="category-filter-select"`.

Why: without this, E2E specs look for elements by visible text or
Tailwind classes. Both change frequently during normal development and
break tests unrelated to the actual change. `data-testid` is
stable against style or copy refactors.

Don't confuse with internal `data-*` attributes of third-party libraries
(e.g. `data-radix-scroll-area-viewport` from Radix UI): those are internal
library mechanisms, not the project's testing convention.

Before declaring a task done, the agent MUST run and leave green:
\`\`\`bash
npm run lint
npm run build
npm run test        # if unit/integration
npm run test -- --coverage  # if coverage targets activated; must meet the configured threshold
npm run test:e2e    # if e2e
\`\`\`
```

**Playwright MCP** (only if the user activated layer 3), registered in Phase 8, step 8.1e
(from `playwright-mcp.settings.tmpl.md`), NOT here: `.claude/settings.json` and the IDE
equivalents don't exist yet in this phase. The MCP is `@playwright/mcp` and lets the agent launch
browsers during implementation and verification:

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

For other agents configured in this project, Phase 8.1e checks each one's MCP registration format
(Cursor: `.cursor/mcp.json`, Windsurf: `.windsurf/mcp.json`). If the format isn't clear for any
agent, it tells the user which files to create and with what content, and waits for confirmation
before writing.

> **Note**: `npx @playwright/mcp` doesn't require an API key. It launches Playwright directly. There are no credentials to protect. It IS reasonable to commit this MCP to the repo so all developers on the team have it.

**Install Playwright browsers** (after `npm install`):

```bash
npx playwright install --with-deps chromium
```

This command downloads the browser. It only needs to be run once per machine. If the user is on CI, the CI workflow also needs this command.

### ✓ PHASE 4.6 COMPLETED

```
Testing stack configured (in memory; everything is written in Phase 8):

  Layers: <unit / integration / e2e, only the activated ones>

  New files:
    <if unit>  vitest.config.ts ✓  (with exclude: e2e/)
    <if unit>  src/test/setup.ts ✓
    <if e2e>   playwright.config.ts ✓
    <if e2e>   e2e/example.spec.ts ✓
    <if POM>   e2e/pages/HomePage.ts ✓ (minimal scaffold)

  Files modified in Phase 8:
    package.json  → test scripts added
    AGENTS.md     → Testing section updated

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

### [USER MESSAGE]
Testing stack configured. Reply **continue** to continue.

### ⏸ PAUSE: Waiting for user to confirm "continue"...

> **📝 PERSISTENCE** (contract `wf-init/lib/state.md`): use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `testing.layers` (activated layers), `testing.runner_detected`, `testing.coverage_threshold` (number or null, if the coverage extra was activated), `testing.visual_regression` (bool), `testing.page_object_model` (bool), `mcps` (project MCPs to configure). Mark `wf_phase_done phase46 <next>`.
> Calculate the next phase based on features:
```bash
NEXT=
if jq -e '.features.ci == true or .features.cd == true or .features.release_please == true' .wizard-state.json >/dev/null; then
  NEXT="phase47-cicd"
else
  NEXT="phase5"
fi
```
> Tell the user: *"Testing stack configured. Reply **continue** to continue."*
> Wait for the response. Only when they confirm, execute in bash:
> - `wf_state_set '.testing.layers' '<activated layers array>'`, e.g. `["unit","integration","e2e"]`
> - `wf_state_set '.testing.runner_detected' '"<runner>"'`, e.g. `"vitest"`, `"playwright"`
> - `wf_state_set '.testing.coverage_threshold' '<number>'`, if coverage extra activated, else `null`
> - `wf_state_set '.testing.visual_regression' 'true'` or `'false'`
> - `wf_state_set '.testing.page_object_model' 'true'` or `'false'`
> - `wf_state_set '.mcps' '<array of selected MCPs>'`

---

═══════════════════════════════════════════════════════
⛔ PHASE 4.6 COMPLETE: Ready for Next Phase
⏸ PAUSE: Waiting for user to confirm "continue"

### [WIZARD ACTION]
When user confirms, run EXACTLY:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Validate state before phase transition (phase-aware validation)
# Note: coverage_threshold can be null if coverage extra not activated - the phase46 validator checks the field exists and is a number when set
NEXT=
if jq -e '.features.ci == true or .features.cd == true or .features.release_please == true' .wizard-state.json >/dev/null; then
  NEXT="phase47-cicd"
else
  NEXT="phase5"
fi
wf_phase_done phase46 "$NEXT"
echo "ℹ Next phase: $NEXT"
cat "$WF_DIR/$NEXT.md"
```
