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

### Resolve the testing profile (framework-aware)

The runner, packages, config and file conventions depend on the framework. They live in one
data file, `templates/protocols/testing/profiles.md`, read through `wf_testing_profile`.
**Never assume React**: take every runner name, package, file convention and script in this
phase from the profile, not from the examples below.

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"
FRAMEWORK=$(jq -r '.discovery.stack.framework // "generic"' .wizard-state.json)
STACK_KEY=$(jq -r '.discovery.stack.stack_key // .discovery.stack_key // "unknown"' .wizard-state.json)
# Second argument: the ecosystem (node | php), because "generic" is a framework token of both.
PROFILE=$(wf_profile_for_framework "$FRAMEWORK" "${STACK_KEY%%-*}")
PROFILE_JSON=$(wf_testing_profile "$PROFILE") || { echo "Cannot read the testing profiles; stopping." >&2; exit 1; }
if [ "$(echo "$PROFILE_JSON" | jq -r '.ecosystem // "npm"')" = "php" ]; then
  RUNNER_FOUND=$(wf_detect_php_runner composer.json)   # pest | phpunit, or empty
else
  RUNNER_FOUND=$(wf_detect_runner package.json)   # vitest | jest | mocha | karma | native, or empty
fi
echo "Framework: $FRAMEWORK -> profile: $PROFILE ($(echo "$PROFILE_JSON" | jq -r .label))"
echo "Existing unit runner (dependency + config): ${RUNNER_FOUND:-none}"

# The frontend of a PHP project (discovery.stack.frontend, never "none" for a Laravel app that
# has React or Vue): it gets its own JS profile and runner, next to the PHP one.
FRONTEND=$(jq -r '.discovery.stack.frontend // "none"' .wizard-state.json)
if [ "${STACK_KEY%%-*}" = "php" ] && [ "$FRONTEND" != "none" ]; then
  FRONTEND_PROFILE=$(wf_profile_for_framework "$FRONTEND")
  FRONTEND_RUNNER_FOUND=$(wf_detect_runner package.json)   # vitest | jest | mocha | karma | native, or empty
  FRONTEND_ROOT=$(jq -r '.testing.frontend_root // empty' .wizard-state.json)
  [ -n "$FRONTEND_ROOT" ] || FRONTEND_ROOT=$(wf_detect_frontend_root .)
  echo "Frontend: $FRONTEND -> profile: $FRONTEND_PROFILE ($(wf_testing_profile "$FRONTEND_PROFILE" | jq -r .label))"
  echo "Frontend sources: ${FRONTEND_ROOT:-not found}"
  echo "Existing frontend runner (dependency + config): ${FRONTEND_RUNNER_FOUND:-none}"
fi
```

**A PHP project with a frontend** (`FRONTEND` is not `none`) is offered a fourth layer, "Frontend unit
tests", next to the PHP layers. It uses the JS profile of its UI framework (`FRONTEND_PROFILE`), not the
PHP one, and it is independent: the PHP runner being kept never keeps the frontend's, and the other way
round. Rules for it:

- `FRONTEND_RUNNER_FOUND` is set: the frontend owns its runner. Install and generate nothing for it,
  record `frontend_runner_existing = true`, and AGENTS.md documents `npm run test`.
- `FRONTEND_ROOT` is empty (none of `resources/js`, `resources/assets/js`, `resources/ts`,
  `resources/assets/ts` exists): ask the developer ONCE which folder holds the JavaScript sources, then
  save the answer as `testing.frontend_root`. Never guess a folder.
- A project whose frontend is not standard (JSX inside `.js`, Laravel Mix or webpack, Babel) is handled
  by the generated config, not by questions: the Vitest config it writes treats the `.js` files under
  the frontend folder as JSX and only runs tests under that folder and `tests/js/`.

| Situation | What the wizard does |
|---|---|
| `RUNNER_FOUND` is set | The project owns its runner. Keep it: nothing installed, no unit config, no `test` script touched. Record `runner_existing = true` and the runner found. The unit/integration layers are still recorded so AGENTS.md documents the conventions. |
| No runner; profile react, next, vue, node-api, nest, laravel or php | Offer the profile's runner. For `laravel` and `php` that is PHPUnit, installed with `composer require --dev` (profile `ecosystem` is `php`); nothing is added to `composer.json` scripts, AGENTS.md documents the profile's `test_command`. |
| No runner; profile angular | The Angular CLI provides the runner. Install and generate nothing; record the layers for the conventions and tell the user to run `ng test` once to confirm. |
| No runner; profile generic | Ask once: Vitest in a node environment, or skip unit tests. |
| Profile has `"e2e": "off"` (node-api, nest, laravel, php) | Do not offer layer 3 (Playwright): API stacks have no browser flow. Offer it only if the user asks. |

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

- Unit/integration: `wf_detect_runner` (above) already applies this rule: the runner dependency AND its config (`vitest.config.*` or a `test:` block in the vite config, `jest.config.*` or a `jest` key in `package.json`, `.mocharc.*`, `karma.conf.*`, an Angular `test` target).
- PHP (profiles `laravel` and `php`): `wf_detect_php_runner` applies the same rule: `pestphp/pest` or `phpunit/phpunit` in `composer.json` (`require` or `require-dev`) AND `phpunit.xml` / `phpunit.xml.dist` (Pest also accepts `tests/Pest.php`). The `grep` above only reads `package.json`, so skip it for these profiles.
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
1. Unit tests: <profile.label>

   WHAT IT DOES: tests functions, services and components in isolation.
   INSTALLS: <profile.packages, comma separated; "nothing" when the project owns its
             runner or the profile has no packages>
   GENERATES: <unit config file printed by wf_unit_config_target; "nothing" when none applies>
   ADDS SCRIPTS: <the keys of profile.scripts; "nothing" when the project owns its runner>
   CONVENTION: <profile.unit_convention>

2. Integration tests: same stack as unit

   WHAT IT DOES: tests several modules together with real dependencies.
   Doesn't require a separate install: uses the layer 1 runner.
   CONVENTION: <profile.integration_convention>
   Requires layer 1 to be activated.

4. Frontend unit tests: <frontend profile label>   (only for a PHP project whose `FRONTEND` is not "none")

   WHAT IT DOES: tests the JavaScript components of the frontend in isolation, in jsdom.
   INSTALLS: <frontend profile packages plus frontend_extra_packages, comma separated; "nothing" when
             the frontend already owns its runner>
   GENERATES: vitest.config.ts scoped to <FRONTEND_ROOT> and tests/js/, a setup file, an example test
   ADDS SCRIPTS: <the keys of the frontend profile's scripts>
   CONVENTION: <frontend profile.unit_convention>

3. E2E tests: Playwright   (omit this entry when the profile has "e2e": "off")

   WHAT IT DOES: complete flows in a real browser (Chromium by default).
   INSTALLS: @playwright/test + browsers via npx playwright install
   GENERATES: playwright.config.ts, e2e/ folder with example spec
   ADDS SCRIPTS: "test:e2e", "test:e2e:ui", "test:e2e:report"
   ENABLES: Playwright MCP so the agent controls the browser during
           implementation and verification.

────────────────────────────────────────────────────────────

What do I activate? [1 / 2 / 1,2 / 1,2,3 / 3 only / 4 (PHP project with a frontend) / none for now]
```

### ⏸ PAUSE: Waiting for user response...

### Optional testing extras (always asked, never activated by default)

Regardless of the layers chosen above, ask if the user wants to
activate any of these extras. They are optional because they have a real cost
(maintenance, execution tokens, or risk of over-engineering in a
small project) that isn't justified in every case. The Decision
Ladder of this same wizard exists precisely to avoid activating things the
project doesn't need yet.

If `runner_existing` is true, do not offer extra 1: the wizard never edits a runner config it does not own.

```
Optional testing extras. None are activated unless you ask:

────────────────────────────────────────────────────────────
1. Configurable coverage targets

   Define a minimum code coverage percentage. If the project
   drops below it, `npm run test -- --coverage` fails locally
   (and in CI, when the Block 6 pipeline exists). Cost: nearly zero.
   It's one config block in the unit config (vitest.config.ts or jest.config.js).

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
coverage threshold block into the unit config in Phase 6b (step B8, from
`coverage-thresholds.tmpl.md`, or `coverage-thresholds.jest.tmpl.md` for Jest, resolving
`{{threshold}}`) and Phase 8 promotes it to the real file;
do NOT edit the unit config here, the file doesn't exist yet in this phase:

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

**If they activated layer 1 or 1+2** (and the wizard owns the runner, i.e. `runner_existing` is not true):

The Builder writes the unit config from the profile in Phase 6b (step B8).
`wf_unit_config_target "$PROFILE" "$RUNNER"` prints its file name: react, next, vue and node-api
(and a generic project that chose Vitest) get `vitest.config.ts`, nest gets `jest.config.js`,
angular gets none. The react and next profiles also stage `src/test/setup.ts`, which their
config lists in `setupFiles`. Phase 8 promotes these files and sets the `test` scripts from the
profile (`scripts` in `profiles.md`). Nothing is written by hand here.

> **Why the Vitest configs exclude `e2e/`**: without it, Vitest picks up Playwright specs in `e2e/` and fails with "Playwright Test did not expect test() to be called here". This happens in any project that activates unit + e2e together.

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

The template targets a Vite dev server. The Builder replaces `http://localhost:5173` and
`npm run dev` with the profile's `dev_port` / `dev_command` when it sets them (next and node-api
3000, nest 3000 with `npm run start:dev`, angular 4200 with `npm start`).

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

**Testing Approach in `AGENTS.md`**: do not write it by hand. The Builder
(`testing_approach_section` in `builder-core.py`) generates the section from the active layers
and the profile: the file conventions (`unit_convention`, `integration_convention`), the
coverage matrix (a backend matrix for API profiles), the E2E guidance, and the `data-testid`
convention only for UI profiles. Before declaring a task done the agent runs `npm run lint`,
`npm run build`, `npm run test` (unit/integration), `npm run test -- --coverage` (when a
coverage threshold is active) and `npm run test:e2e` (e2e).

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
    <if unit, wizard owns the runner>  <unit config from the profile> ✓  (Vitest configs exclude e2e/)
    <if react or next profile>         src/test/setup.ts ✓
    <if runner_existing>               nothing for the unit layer: the project keeps its <runner>
    <if e2e>   playwright.config.ts ✓
    <if e2e>   e2e/example.spec.ts ✓
    <if POM>   e2e/pages/HomePage.ts ✓ (minimal scaffold)

  Files modified in Phase 8:
    package.json  → test scripts added (not when the project owns its runner)
    AGENTS.md     → Testing section updated

  Playwright MCP:
    <if e2e>  .claude/settings.json (and IDE equivalents) ← Phase 8

  Activated extras:
    <if coverage>          - Minimum coverage: <threshold>%
    <if visual regression> - Visual regression (snapshots) active
    <if POM>                - Page Object Model active

  Final checks_before_done (Node profiles; a PHP profile lists `vendor/bin/pint --dirty --test` and
  `vendor/bin/phpstan analyse` when the project uses them, plus the profile's test_command, plus
  `npm run test` when the frontend layer is active):
    - npm run lint
    - npm run build
    <if unit>      - npm run test
    <if coverage>  - npm run test -- --coverage
    <if e2e>       - npm run test:e2e
```

### [USER MESSAGE]
Testing stack configured. Reply **continue** to continue.

### ⏸ PAUSE: Waiting for user to confirm "continue"...

> **📝 PERSISTENCE** (contract `wf-init/lib/state.md`): use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `testing.layers` (activated layers), `testing.profile`, `testing.runner`, `testing.runner_existing`, `testing.environment`, `testing.test_pattern`, `testing.runner_detected`, `testing.coverage_threshold` (number or null, if the coverage extra was activated), `testing.visual_regression` (bool), `testing.page_object_model` (bool), `mcps` (project MCPs to configure). Mark `wf_phase_done phase46 <next>`.
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
> - `wf_state_set '.testing.profile' "\"$PROFILE\""`
> - `wf_state_set '.testing.runner' '"<runner>"'`: the runner found (`$RUNNER_FOUND`), else the profile's `runner` (for generic, the one the user chose); `null` when there is none
> - `wf_state_set '.testing.runner_existing' 'true'` when `RUNNER_FOUND` is set, else `'false'`
> - `wf_state_set '.testing.environment' '"<jsdom|node>"'`: the profile's `environment` (`null` for angular and for a generic project without a runner)
> - `wf_state_set '.testing.test_pattern' '"<profile.unit_convention>"'`
> - for the "Frontend unit tests" layer (only a PHP project with a frontend): add `"frontend"` to `testing.layers`, and save `wf_state_set '.testing.frontend_profile' "\"$FRONTEND_PROFILE\""`, `wf_state_set '.testing.frontend_runner' '"<runner>"'` (the one found, else the profile's `runner`; `null` when none), `wf_state_set '.testing.frontend_runner_existing' 'true'` when `FRONTEND_RUNNER_FOUND` is set, else `'false'`, and `wf_state_set '.testing.frontend_root' "\"$FRONTEND_ROOT\""` (the detected folder or the one the developer gave)
> - `wf_state_set '.testing.test_command' '"<profile.test_command>"'`, only for a profile that has one (`laravel`, `php`); the Node profiles keep `null` because their command is the `test` script
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
