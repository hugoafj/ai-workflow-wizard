# /wf-settings — Optional workflow settings wizard

> **When to use**: when you want to change something you chose during
> `/wf-init` and are no longer happy with: enable or disable the testing
> infrastructure, add or remove a testing extra, enable or disable the
> Decision Ladder, toggle CI/CD, choose the release strategy, or add/remove
> an IDE/CLI.
>
> **Difference from `/wf-refresh`**: `wf-refresh` updates your AGENTS.md
> when the *wizard template* changed (new version) or the *project*
> changed (new dependencies, etc.). `wf-settings` is different: nothing
> changed in the project or the wizard — it is you who decides to change
> a preference you already chose before.

---

## Agent role during settings adjustment

You are a settings wizard. Your goal is for the developer to see at a
glance which optional modules are active today, and change only the ones they
want — without touching anything else in the project.

**Inviolable rules**:

1. Never change something the user did not explicitly select.
2. Always show the current state before asking what to change — never
   assume the user remembers what they chose in `/wf-init`.
3. Each change is applied and confirmed individually before asking
   if the user wants to adjust something else — do not accumulate changes without showing them.
4. Never `git push`. The final commit follows the same review gate as
   the rest of this workflow.
5. If a change requires running something outside this repo (for example,
   `gentle-ai sync`), warn before running it.

---

## PHASE 1 — Read the current state

Before asking anything, read the actual project configuration from
`.wizard-state.json` — it is the wizard's source of truth (contract
`wf-init/lib/state.md`). NEVER trust what `AGENTS.md` documents
as "originally chosen", as it may be out of date.

**ABSOLUTE RULE**: this phase is internal READ only. NEVER show the
user raw output from jq, grep, cat, ls, or any other command.
If a field does not exist in the state, treat that feature as OFF and continue.
The user should only see the menu in Phase 2.

```bash
# Read full wizard state
cat .wizard-state.json 2>/dev/null

# Or read individual fields:
jq -r '.features.decision_ladder // false' .wizard-state.json 2>/dev/null
jq -r '.features.testing // false' .wizard-state.json 2>/dev/null
jq -r '.features.ci // false' .wizard-state.json 2>/dev/null
jq -r '.features.release_please // false' .wizard-state.json 2>/dev/null
jq -r '.testing.coverage_threshold // null' .wizard-state.json 2>/dev/null
jq -r '.testing.visual_regression // false' .wizard-state.json 2>/dev/null
jq -r '.testing.page_object_model // false' .wizard-state.json 2>/dev/null
jq -r '.ci.e2e_in_ci // false' .wizard-state.json 2>/dev/null
jq -r '.ci.ai_reviewer // "none"' .wizard-state.json 2>/dev/null
jq -r '.ci.gga_provider // "none"' .wizard-state.json 2>/dev/null
jq -r '.ci.security_review // false' .wizard-state.json 2>/dev/null
jq -r '.ci.auto_improve // true' .wizard-state.json 2>/dev/null
jq -r '.ci.inline_suggestions // true' .wizard-state.json 2>/dev/null
```

**If `.wizard-state.json` does not exist**: the project was not initialized with
`/wf-init`. Inform the user they need to run `/wf-init` first.

**If any field does not exist** (project with an older wizard version):
treat it as OFF and continue — do not show errors to the user.

Build the real state internally, and only show the menu (Phase 2).

---

## PHASE 2 — Show the settings menu

Show the menu with the current state of each option. The user writes the
number of the option they want to adjust.

**MENU FORMAT — CRITICAL**:

1. NEVER use code blocks (```) or markdown formatting for the menu.
2. Show it as plain text, ONE line per option.
3. **FIXED NUMBERING — NEVER renumber**: always show all 14 options with the
   numbers below, because each number maps to the `### N:` section in Phase 3.
   Never hide an option or compact the numbers. An option that does not apply
   is shown as `n/a (<reason>)`:
   - 3, 4, 5 (testing extras): `n/a (testing is OFF)` when option 2 is OFF
   - 7, 8, 9, 10 (CI sub-options): `n/a (CI is OFF)` when option 6 is OFF
   - 11 (release-please standalone): `n/a (included in CI)` when option 6 is ON
4. If the user picks an `n/a` option, explain why it does not apply (and which
   option enables its parent) and apply nothing.
5. If the IDE collapses the lines, repeat until it displays correctly.

Example of how it should look:

Workflow settings, current state:

1. wf-ladder (Decision Ladder): <ON/OFF>
2. Testing infrastructure: <ON/OFF>
3. Coverage targets: <80%/OFF>
4. Visual regression: <ON/OFF>
5. Page Object Model: <ON/OFF>
6. CI: <ON/OFF>
7. AI Reviewer: <GGA (provider: X) / Copilot / Claude Code / Gemini / None>
8. AI Review Suggestions: <ON/OFF> (Gemini: auto_improve / Claude: inline comments)
9. Dedicated Security Review: <Claude/Gemini/OFF>
10. E2E in CI: <ON/OFF>
11. release-please standalone: <ON/OFF>
12. CD (automatic deploy): <ON/OFF>
13. Release strategy: <tag v* / push a main>
14. IDEs/CLIs: <comma-separated active list>

Which number do you want to adjust?

End of example.

**Wait for user response.**

If they choose several (e.g. "1, 3"), process one at a time, in the order the
user wrote them — never in parallel, so each confirmation is
clear.

---

## PHASE 3 — Apply the chosen change

For each option, the flow is:
1. Show the current state of that option
2. Ask if they want to keep or change
3. If they change, show available options and wait for choice
4. Apply and confirm

**CRITICAL RULE — Synchronized state**: every change you apply MUST
also update `.wizard-state.json` (contract `wf-init/lib/state.md`).
If you only modify AGENTS.md or config files but not the state, the next
run of `/wf-init` or `/wf-refresh` will read outdated state and may
undo your change. Use `jq` or `edit` to update the corresponding
field in `.wizard-state.json` after each change.

---

### 1: wf-ladder

```
wf-ladder (Decision Ladder): <ON / OFF>

Do you want to keep it as is or change it?
  [keep / change]
```

**If they choose keep**: move to the next option (if they chose several).

**If they want to change (enable)**: inject the `wf-ladder` section into
`AGENTS.md` (same content that `wf-init.md` documents in its Behavior
Preferences phase, Question 4) and generate the `/wf-ladder` command for
active IDEs if it does not already exist. **Update the
footer**'s `features:`
line (single line, comma-separated — see `templates/AGENTS.router.md`) so its
`ladder=` token becomes `ladder=yes`:

```bash
sed -i.bak -E 's/(features: [^|]*ladder=)[a-z]*/\1yes/' AGENTS.md && rm AGENTS.md.bak
```

**If they want to change (disable)**: ask first, because it is an
anti-over-engineering heuristic — removing it is not neutral:

```
wf-ladder helps the agent avoid over-engineering on small
changes. Without it, the agent loses that explicit check before
implementing. Do you confirm you want to remove it? [yes / no]
```

**Wait for explicit confirmation before removing it.** If confirmed, remove the
section from `AGENTS.md` (do not delete the `/wf-ladder` command
file). **Update the footer**'s `ladder=` token to `no` (same `sed` pattern above with `no`).

Confirm:
```
✓ wf-ladder: <enabled / disabled>
✓ .wizard-state.json: features.decision_ladder = <yes/no>
✓ AGENTS.md footer updated
```

**State update**:
```bash
# Replace <value> with true or false
jq '.features.decision_ladder = <value>' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 2: Testing infrastructure

```
Testing infrastructure: <ON / OFF>

Do you want to keep it as is or change it?
  [keep / change]
```

**If they choose keep**: move to the next option.

**If they want to change (enable)**: set up the test infrastructure the same way
`wf-init.md` Phase 4.6 does (detect the test runner, then configure the unit,
integration, and E2E layers the user chooses). Add the `## Testing Approach`
section to `AGENTS.md`, using the verbatim content of
`templates/protocols/testing/testing-approach.section.md`.

After enabling, ask about options:

```
Testing enabled. Do you want to configure these options?
3. Coverage targets      <percentage / OFF>      [current: OFF]
4. Visual regression     <ON / OFF>              [current: OFF]
5. Page Object Model     <ON / OFF>              [current: OFF]

Which one do you configure? [3 / 4 / 5 / none]
```

**If they want to change (disable)**: remove the `## Testing Approach` section
from `AGENTS.md`. Do not delete test configs or specs; they stay in the project.

Confirm:
```
✓ Testing infrastructure: <enabled / disabled>
✓ .wizard-state.json: features.testing = <yes/no>
```

**State update**:
```bash
# Replace <value> with true or false
jq '.features.testing = <value>' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 3: Coverage targets

```
Coverage targets: <ON (threshold: N%) / OFF>

Do you want to keep or change?
  [keep / change to <new_threshold>% / disable]
```

**If enabling**: ask for the threshold (same as in `wf-init.md` Phase 4.6) and
add the `coverage.thresholds` block to `vitest.config.ts`. Write the threshold
only to `vitest.config.ts` and to `.wizard-state.json` (`testing.coverage_threshold`,
see the state update below).

**If disabling**: remove the `coverage.thresholds` block from `vitest.config.ts`
and set `testing.coverage_threshold` to `null` in `.wizard-state.json`.

Confirm:
```
✓ Coverage targets: <enabled (threshold: N%) / disabled>
```

**State update**:
```bash
# If enabling (replace N with the threshold):
jq '.testing.coverage_threshold = N' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json

# If disabling:
jq '.testing.coverage_threshold = null' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 4: Visual regression

```
Visual regression: <ON / OFF>

Do you want to keep or change?
  [keep / enable / disable]
```

**If enabling**: add the snapshot config to `playwright.config.ts`
(same as in `wf-init.md` Phase 4.6).

**If disabling**: remove that config. Ask if they also want to delete the
already generated reference images (`e2e/**/*.png` from snapshots) — do not
delete them without confirmation, they might want to reuse them.

Confirm:
```
✓ Visual regression: <enabled / disabled>
```

**State update**:
```bash
# Replace <value> with true or false
jq '.testing.visual_regression = <value>' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 5: Page Object Model

```
Page Object Model: <ON / OFF>

Do you want to keep or change?
  [keep / enable / disable]
```

**If enabling**: generate `e2e/pages/` with a minimal example if it does not exist.

**If disabling**: inform that this is only a code convention, there
is nothing to "uninstall" — if you already have specs using the pattern, removing
the convention does not rewrite them automatically. Ask if they want the
agent to rewrite them without POM (a separate task, do not do it without being asked).

Confirm:
```
✓ Page Object Model: <enabled / disabled>
```

**State update**:
```bash
# Replace <value> with true or false
jq '.testing.page_object_model = <value>' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 6: CI

```
CI: <ON / OFF>

Do you want to keep or change?
  [keep / change]
```

**If they choose keep**: move to the next option.

**If they want to change (enable)**:

**Case A — release-please standalone is OFF** (`features.release_please == false`):

```
Enable full CI? This will add:
  - Conventional commits + release-please
  - Quality Guard
  - Optional AI Reviewer, Security Review, and E2E in CI

[yes / no]
```

If yes, update state and continue to the options 7-12 to configure AI reviewer,
security review, and E2E. When finished, run `/wf-refresh` to regenerate the
CI/CD artifacts and `AGENTS.md`.

```bash
jq '.features.ci = true |
    .features.release_please = true |
    .ci.conventional_commits = true |
    .ci.release_please = true |
    .ci.ai_reviewer = "none" |
    .ci.gga_provider = "none" |
    .ci.security_review = false |
    .ci.e2e_in_ci = false |
    .ci.auto_improve = true |
    .ci.inline_suggestions = true |
    .ci.release_ai_summary = false |
    .ci.release_ai_provider = "none"' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

**Case B — release-please standalone is ON** (`features.release_please == true` and `features.ci == false`):

```
You already have release-please standalone active. Enabling full CI subsumes it
and adds Quality Guard + optional AI review and security review.

Enable full CI? [yes / no]
```

If yes, update state and continue to options 7-12, then run `/wf-refresh`.

```bash
jq '.features.ci = true |
    .features.release_please = true |
    .ci.conventional_commits = true |
    .ci.release_please = true' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

**If they want to change (disable)**:

```
CI is currently active. What do you want to do?

[migrate]    Keep release-please standalone (conventional commits + auto-release,
             remove quality guard, AI review, and security review).
[disable]    Disable the entire CI pipeline (remove all workflows and hooks).
```

**If they choose `migrate`**:

Set `features.ci = false`, keep `features.release_please = true`, and clear only
the full-CI fields. Then run `/wf-refresh` to remove quality-guard/AI/security
workflows while preserving release-please.

```bash
jq '.features.ci = false |
    .features.release_please = true |
    .ci.ai_reviewer = "none" |
    .ci.gga_provider = "none" |
    .ci.security_review = false |
    .ci.e2e_in_ci = false |
    .ci.auto_improve = true |
    .ci.inline_suggestions = true |
    .ci.release_ai_summary = false |
    .ci.release_ai_provider = "none"' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

**If they choose `disable everything`**:

Set both CI and release-please to false and clear the `ci` object. Then run
`/wf-refresh` to remove all CI/CD workflows.

```bash
jq '.features.ci = false |
    .features.release_please = false |
    .ci = {}' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

> **Do NOT run `phase47-cicd.md` from `/wf-settings`** — that file belongs to the
> `/wf-init` phase flow and is not downloaded in this command context. CI changes
> are applied by updating state and running `/wf-refresh`.

Confirm:
```
✓ CI: <enabled / migrated to standalone / disabled>
✓ .wizard-state.json: features.ci = <true/false>, features.release_please = <true/false>
✓ CI/CD artifacts regenerated via /wf-refresh
```

---

### 7: AI Reviewer

> Only available if CI = ON.
> **Single source**: the complete option text and per-option generation logic live in
> `templates/protocols/cicd/_base.md` (PHASE 1). If a provider's details change, change them
> there; this option only adapts the summary and delegates generation.

```
Current AI Reviewer: <GGA (provider: X) / Copilot / Claude / Gemini / None>

Do you want to keep or change?
  [keep / change]
```

**If they choose keep**: move to the next option.

**If they want to change**: show the options:

```
Which AI reviewer do you want to use for your PR reviews?

────────────────────────────────────────────────────────────

GGA — Recommended
  Provider agnostic: Claude, Gemini, and Codex are pre-mapped in `gga-review.yml.md`.
  Other providers (including OpenCode) can be used by adding the corresponding CLI/secret mapping.
  Flexible modes: local (on your machine) + CI (in GitHub Actions)
  Native integration with gentle-ai and this workflow

GitHub Copilot
  Integrated directly into GitHub, no additional configuration
  Less flexible than GGA but simpler if you already use Copilot

Claude Code
  Requires Anthropic API key
  High quality but more expensive than other options
  Generates: claude-review.yml

Gemini
  Requires Google API key (FREE with quota)
  Good cost/quality balance
  Generates: gemini-review.yml

None
  No automatic AI review — only Quality Guard (lint + build + tests)

────────────────────────────────────────────────────────────
Which one do you prefer?
```

**If they choose GGA**: ask for the provider:

```
Which provider do you want to use with GGA?

1. Claude (Anthropic)     → claude
2. Gemini (Google)        → gemini
3. Codex (OpenAI)         → codex

Provider keys must match the `gga_provider` values supported by `gga-review.yml.md`.
Which one? [1-3]
```

**If they choose another** (Copilot, Claude, Gemini, None): no additional provider needed.

**Apply the change**:

- If GGA: remove direct review workflows (`claude-review.yml`,
  `gemini-review.yml`) if they exist. Generate/update
  `.github/workflows/gga-review.yml` from the template
  `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/gga-review.yml.md`. If it already existed,
  regenerate it with the new provider.
- If Copilot: remove `gga-review.yml` and direct review workflows.
  No own workflow is generated — the review comes integrated in GitHub.
  Inform the user they must enable Copilot in their repo if they do not have it.
- If Claude (direct, without GGA): remove `gga-review.yml` if it exists.
  Generate `.github/workflows/claude-review.yml` from the template
  `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/claude-review.yml.md`.
- If Gemini (direct, without GGA): remove `gga-review.yml` if it exists.
  Generate `.github/workflows/gemini-review.yml` from the template
  `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/gemini-review.yml.md`.
  Also generate `.pr_agent.toml` from
  `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/pr-agent-config.toml.md` (required
  for pr-agent to run on `synchronize` and `reopened`).
- If None: remove `.github/workflows/gga-review.yml`,
  `claude-review.yml`, `gemini-review.yml` if they exist.

**Update state**:
```bash
jq '.ci.ai_reviewer = "<selection>"' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
# If GGA, also:
jq '.ci.gga_provider = "<provider>"' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

Confirm:
```
✓ AI Reviewer changed to: <selection>
✓ .wizard-state.json: ci.ai_reviewer = <value>
✓ <if GGA> .github/workflows/gga-review.yml regenerated with provider <X>
✓ <if Claude> .github/workflows/claude-review.yml generated
✓ <if Gemini> .github/workflows/gemini-review.yml generated
✓ <if Gemini> .pr_agent.toml generated
✓ <if None> review workflows removed
```

---

### 8: AI Review Suggestions

> Only available if CI = ON and AI reviewer is Gemini or Claude.

```
AI Review Suggestions: <ON / OFF>

Do you want to keep or change?
  [keep / change]
```

**If they choose keep**: move to the next option.

**If they want to change**: show the current state and explain what it does:

```
Current state: <ON / OFF>

What this option does:
  Gemini (auto_improve): generates suggestions with diffs ready to apply
    directly in the PR. More noise but more action.
  Claude (inline comments): allows Claude to create inline comments
    on specific lines of code. More precise than a general comment.

Enable or disable? [enable / disable]
```

**If enable (Gemini)**:
```bash
jq '.ci.auto_improve = true' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```
Regenerate `gemini-review.yml` with `auto_improve: "true"`.

**If disable (Gemini)**:
```bash
jq '.ci.auto_improve = false' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```
Regenerate `gemini-review.yml` with `auto_improve: "false"`.

**If enable (Claude)**:
```bash
jq '.ci.inline_suggestions = true' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```
Regenerate `claude-review.yml` with `claude_args` including `--allowedTools`.

**If disable (Claude)**:
```bash
jq '.ci.inline_suggestions = false' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```
Regenerate `claude-review.yml` without `claude_args`.

Confirm:
```
✓ AI Review Suggestions: <enabled / disabled>
✓ .wizard-state.json: ci.auto_improve / ci.inline_suggestions = <value>
✓ <workflow> regenerated
```

---

### 9: Dedicated Security Review

> Only available if CI = ON.
> **Single source**: the question text and artifact names live in
> `templates/protocols/cicd/_base.md` (PHASE 3).

```
Dedicated Security Review: <Claude / Gemini / OFF>

Do you want to keep or change?
  [keep / change]
```

**If they choose keep**: move to the next option.

**If they want to change (enable)**: show the options:

```
Do you want to add a dedicated security review in addition to the standard
AI reviewer?

────────────────────────────────────────────────────────────

Claude — Security review with Anthropic
  High quality for security analysis

Gemini — Security review with Google
  Good cost/quality balance

None — Recommended
  The standard AI reviewer already covers basic security aspects

───────────────────────────────────────────────────────────
Which one do you prefer?
```

**If they choose Claude or Gemini**: generate/update
`https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/security-review.<provider>.yml.md` as
`.github/workflows/security-review.yml`. Use PR-Agent with the selected
provider.

**If they choose None**: disable (remove the workflow if it exists).

**Update state**:
```bash
# If enabling with provider:
jq '.ci.security_review = "<provider>"' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json

# If disabling:
jq '.ci.security_review = false' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

Confirm:
```
✓ Dedicated Security Review: <enabled (provider: X) / disabled>
✓ .wizard-state.json: ci.security_review = <"claude"/"gemini"/false>
✓ <if active> .github/workflows/security-review.yml regenerated
✓ <if disabled> .github/workflows/security-review.yml removed
```

---

### 10: E2E in CI

> Only available if CI = ON and the project has E2E layer detected.

```
E2E in CI: <ON / OFF>

Do you want to keep or change?
  [keep / enable / disable]
```

**If enabling**: include `npm run test:e2e` in the CI quality guard.
May lengthen the pipeline (2-10min additional).

**If disabling**: remove `npm run test:e2e` from the quality guard. The e2e
script still exists for local use.

Confirm:
```
✓ E2E in CI: <enabled / disabled>
```

**State update**:
```bash
jq '.ci.e2e_in_ci = <value>' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 11: release-please standalone

> Only applicable if CI = OFF. If CI is active, release-please is already
> included: the menu shows this option as `n/a (included in CI)` and, if the
> user picks it, explain that and apply nothing.
> **Single source**: the question text and artifact names live in
> `templates/protocols/cicd/_base.md` (PHASE 5).

```
release-please standalone: <ON / OFF>

Do you want to keep or change?
  [keep / change]
```

**If they choose keep**: move to the next option.

**If they want to change (enable)**: configure conventional commits + Husky +
release-please. Ask if they want AI summary for the release PR (optional).
Set `state.ci.release_please = true`. **Update the footer** to
`release=yes`.

**If they want to change (disable)**: remove the conventional commits and
release-please configuration. **Update the footer** to `release=no`.

Confirm:
```
✓ release-please standalone: <enabled / disabled>
✓ .wizard-state.json: features.release_please = <yes/no>
✓ .wizard-state.json: ci.release_please = <yes/no>
✓ .wizard-state.json: ci.conventional_commits = <yes/no>
✓ AGENTS.md footer updated
```

**State update**:
```bash
jq '.features.release_please = <value> | .ci.release_please = <value> | .ci.conventional_commits = <value>' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 12: CD (automatic deploy)

```
CD (automatic deploy): <ON / OFF>

Do you want to keep or change?
  [keep / change]
```

**If they choose keep**: move to the next option (if they chose several).

**If they want to change (enable)**:

CD is **independent** of CI — it can be activated without CI configured.

Ask:

```
Detected stack: <Laravel + Node / Laravel / Pure Node>
Correct? [yes / correct]
```

Then ask about trigger, platform, runtime (Nginx/Apache/Docker/PM2) and deploy path
(same questions as phase47 PART B). Set `state.cd.enabled = true` and the corresponding
fields, then run `/wf-refresh` to regenerate `.github/workflows/deploy.yml`.
Do NOT run `phase47-cicd.md` from `/wf-settings` — that file belongs to the `/wf-init` phase flow.

**If they want to change (disable)**:

```
CD is currently active. Do you want to disable automatic deploy?

This removes the deploy.yml workflow from GitHub Actions. Your app
will continue running on the server but will not be deployed
automatically.

[yes, disable / no, keep]
```

If confirmed: set `state.cd.enabled = false`, remove `deploy.yml` from
`.github/workflows/` if it exists. **Update the footer** to `cd=no`.

Confirm:
```
✓ CD: <enabled / disabled>
✓ .wizard-state.json: features.cd = <yes/no>
✓ AGENTS.md footer updated
```

**State update**:
```bash
jq '.features.cd = <value> | .cd.enabled = <value>' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 13: Release strategy

> Always available. Affects the wizard's CD (if active) and documents
> the decision for external CD (AWS CodePipeline, Vercel, Railway, etc.).

```
Release strategy: <tag v* / push a main>

Do you want to keep or change?
  [keep / change]
```

**If they choose keep**: move to the next option.

**If they want to change**:

```
When does the deploy execute?

  1. On merging a tag v* (recommended if you use release-please)
  2. On push to main (every merge to main deploys)

  [1 / 2]
```

**If they choose tag (1)** and release-please is OFF → inform:
```
To use tags you need release-please to generate them
automatically. Should I activate it too? [yes / no]
```
If yes: set `state.features.release_please = true`,
`state.ci.conventional_commits = true`, `state.ci.release_please = true`,
and `state.cd.trigger = 'tag'`. Update the AGENTS.md footer to `release=yes`.
If no: do not change the trigger (stays as push to main).

**If they choose push a main (2)**: no restrictions. Set `state.cd.trigger = 'push_main'`.

**If wizard CD is ON**: regenerate `.github/workflows/deploy.yml` with the new trigger
(`tags: ['v*']` or `branches: [main]`).

**If wizard CD is OFF** (external CD or no CD): the wizard informs the user
what to configure in their external tool:
- **AWS CodePipeline**: configure the Source stage to listen for `v*` tag events
  or push to `main` branch, depending on the choice.
- **Vercel/Railway/Fly.io**: these platforms automatically detect push to main
  and tags — no manual trigger configuration required.
- **Custom CD**: use the corresponding event (GitHub webhook `push` with
  ref filter).

Confirm:
```
✓ Release strategy changed to: <tag v* / push a main>
✓ .wizard-state.json: cd.trigger = <tag / push_main>
✓ <if release-please activated> .features.release_please = true, .ci.conventional_commits = true, .ci.release_please = true
✓ <if release-please activated> AGENTS.md footer updated to release=yes
✓ <if CD ON> .github/workflows/deploy.yml regenerated
✓ <if CD OFF> Instructions for configuring your external CD
```

**State update**:
```bash
# For tag trigger without release-please:
jq '.features.release_please = true |
    .ci.conventional_commits = true |
    .ci.release_please = true |
    .cd.trigger = "tag"' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
sed -i.bak -E 's/(features: [^|]*release=)[a-z]*/\1yes/' AGENTS.md && rm AGENTS.md.bak

# For push_main trigger (or when release-please is already active):
jq '.cd.trigger = "<new_trigger>"' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 14: IDEs/CLIs

```
IDEs/CLIs: <comma-separated active list>

Do you want to add or remove an IDE/CLI?
  [add / remove]
```

This option toggles which IDEs/CLIs this project's wizard artifacts are generated for.
Adding an IDE creates EVERYTHING related for it (satellite, commands, native skills, and the
Windsurf fix if applicable); removing an IDE deletes EVERYTHING related. Only project files
are touched — never `~/.<ide>/` (global gentle-ai config).

**Source**: the templates are downloaded from the wizard's raw template root
`https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main` (the same source the
Builder uses). If a `$WF_RAW` variable is already defined in this session, prefer it —
`WF_RAW="${WF_RAW:-https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main}"`.
Always read the current list from `state.answers.ides`
(`jq -r '.answers.ides[]' .wizard-state.json`) — never assume what was chosen in `/wf-init`.

**If they choose `add`**:

```
Which IDE/CLI do you want to add?
  1. Claude Code
  2. Cursor
  3. Windsurf / Devin
  4. Kiro
  5. OpenCode
  6. GitHub Copilot (VS Code)
  7. Gemini CLI
  8. Codex
  9. Antigravity CLI

Which one? [1-9]
```

Generate everything related for the chosen IDE, downloading from `$WF_RAW`:

1. **Satellite** — `$WF_RAW/templates/satellites/<satellite>.tmpl` where the satellite
   filename is mapped from the IDE key:
   `claude-code` → `claude`, `vscode-copilot` → `copilot`, `gemini-cli` → `gemini`,
   `cursor` → `cursor`, `windsurf` → `windsurf`, `kiro` → `kiro`,
   `antigravity` → `antigravity`. Destination (route table in protocol `ides`):
   `claude-code` → `CLAUDE.md`, `vscode-copilot` → `.github/copilot-instructions.md`,
   `cursor` → `.cursor/rules/project.mdc`, `windsurf` → `.windsurf/rules/project.md`,
   `kiro` → `.kiro/steering/project-context.md`, `gemini-cli` → `GEMINI.md`,
   `antigravity` → `ANTIGRAVITY.md`. Create parent directories as needed.
2. **Commands**: every command in the catalog (full command catalog from Builder B7: 3-4 commands depending on active features) → the IDE's
    command directory
    (`.claude/commands/`, `.cursor/commands/`, `.windsurf/workflows/`, `.kiro/steering/`,
    `.opencode/commands/`, `.github/prompts/` **with `.prompt.md` suffix**, `.codex/commands/`), applying the per-IDE
    frontmatter (protocol `ides`, routing-table.section.md).
3. **Skills** — the packaged protocol skills → the IDE's native skills directory
    (`.claude/skills/`, `.cursor/skills/`, `.kiro/skills/`, `.codex/skills/`, `.windsurf/skills/`, `.devin/skills/`, `.gemini/skills/`, `.opencode/skills/`, `.agents/skills/`, `.github/skills/`).

Confirm:
```
✓ <IDE> added
✓ Satellite: <path>
✓ Commands: <N> generated in <dir>
✓ Skills: <N> generated in <dir>
```

**State update**:
```bash
jq '.answers.ides += ["<ide>"]' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

**If they choose `remove`**:

```
Which IDE/CLI do you want to remove?
  <numbered list of the current active IDEs>

Which one? [1-N]
```

Delete everything related for the chosen IDE, confirming first:

```
Removing <IDE> deletes:
  - <satellite path>
  - <N> commands in <command dir>
  - <N> skills in <skills dir>

Confirm deletion? [yes / no]
```

- Delete ONLY the files this wizard generated in the project (satellite, commands, skills).
  Never touch `~/.<ide>/` or gentle-ai's global config.
- If some of the files are already gone, just remove what exists and update the state.

Confirm:
```
✓ <IDE> removed
✓ <satellite path> deleted
✓ <N> commands deleted
✓ <N> skills deleted
```

**State update**:
```bash
jq '.answers.ides -= ["<ide>"]' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

**If they say something other than `add` or `remove`**: show the current list again and
repeat the question. Do not guess.

---

---

## PHASE 4 — Anything else?

After applying each change (one at a time, if the user chose several in
Phase 2), ask:

```
✓ <summary of the change just applied>

Do you want to adjust anything else? [yes, another / no, I am done]
```

**If they say "yes, another"**: show the full Phase 2 menu again (with
the state now updated reflecting the change just made), and repeat.

**If they say "no, I am done"**: continue to Phase 5.

---

## PHASE 5 — Final summary and commit

Show the consolidated summary of ALL changes made in this session
(can be one or several, from different Phase 4 rounds):

```
Session settings summary:
  ✓ wf-ladder: enabled
  ✓ Coverage targets: 80%

Modified files:
  AGENTS.md
  vitest.config.ts

Do I write these changes and make the commit? [yes / no, abort / let me edit X first]
```

**PAUSE — Wait for explicit confirmation before writing anything.**

If confirmed:
```bash
git add <modified files>
git commit -m "chore: update workflow settings

<list of changes, one per line>"
```

**Does NOT `git push`** — same as the rest of this workflow's wizards.

---

## Implementation notes for the agent

- **Always read the real state before showing the menu** (Phase 1) — do not
  assume that `AGENTS.md` faithfully reflects `.wizard-state.json` or the
  coverage block in `vitest.config.ts`. They may have diverged if someone
  edited one without the other.
- **Each change is confirmed individually** before asking "anything
  else?" — do not silently process several changes and show everything together at the
  end, except in the Phase 5 summary, which is consolidated.
- **Never delete reference files (visual regression snapshots,
  specs with POM)** when disabling an extra without asking first — the
  config disablement does not imply the user wants to lose that
  content.
- **If the user interrupts or says "stop"** at any phase, stop
  completely. Do not auto-complete phases.
- **Do not push** under any circumstances.

---


