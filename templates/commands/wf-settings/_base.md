# /wf-settings — Optional workflow settings wizard

> **When to use**: when you want to change something you chose during
> `/wf-init` and are no longer happy with — enable or disable strict TDD
> mode, add or remove a testing extra, enable or disable the Decision
> Ladder, or change the SDD persistence backend.
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
jq -r '.features.tdd_protocol // false' .wizard-state.json 2>/dev/null
jq -r '.features.routing_abc // false' .wizard-state.json 2>/dev/null
jq -r '.features.ci // false' .wizard-state.json 2>/dev/null
jq -r '.features.release_please // false' .wizard-state.json 2>/dev/null
jq -r '.sdd.backend // "unknown"' .wizard-state.json 2>/dev/null
jq -r '.testing.tdd_mode // "standard"' .wizard-state.json 2>/dev/null
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

Show the menu with the current state of each option. Sub-options only
appear if the parent is active. The user writes the number of the option
they want to adjust.

**MENU FORMAT — CRITICAL**:

1. NEVER use code blocks (```) or markdown formatting for the menu.
2. Show it as plain text, ONE option per line, sequential numbering.
3. If the IDE collapses the lines, repeat until it displays correctly.

Example of how it should look:

Workflow settings — current state:

1. wf-ladder (Decision Ladder) — <ON/OFF>
2. TDD — <ON/OFF>
3. TDD Mode — <standard/strict>
4. Coverage targets — <80%/OFF>
5. Visual regression — <ON/OFF>
6. Page Object Model — <ON/OFF>
7. wf-sdd-trigger (SDD-forcing policy) — <ON/OFF>
8. SDD persistence backend — <engram/openspec/hybrid>
9. CI — <ON/OFF>
10. AI Reviewer — <GGA (provider: X) / Copilot / Claude Code / Gemini / None>
11. AI Review Suggestions — <ON/OFF> (Gemini: auto_improve / Claude: inline comments)
12. Dedicated Security Review — <Claude/Gemini/OFF>
13. E2E in CI — <ON/OFF>
14. release-please standalone — <ON/OFF>
15. CD (automatic deploy) — <ON/OFF>
16. Release strategy — <tag v* / push a main>
<if Windsurf is in active IDEs>
17. Fix Windsurf gentle-ai — <Reapply workaround>
</if>
18. IDEs/CLIs — <comma-separated active list>

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

### Option 1 — wf-ladder

```
wf-ladder (Decision Ladder): <ON / OFF>

Do you want to keep it as is or change it?
  [keep / change]
```

**If they choose keep**: move to the next option (if they chose several).

**If they want to change (enable)**: inject the `wf-ladder` section into
`AGENTS.md` (same content that `wf-init.md` documents in its Behavior
Preferences phase, Question 4) and generate the `/wf-ladder` command for
active IDEs if it does not already exist. Ensure `wf-orchestrator` is also
present (it must be built whenever `wf-ladder`, `wf-sdd-trigger`, or `wf-tdd`
is active). **Update the footer**'s `features:`
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
If no other `wf-` protocol remains active (`routing`, `tdd`), also remove `wf-orchestrator`.

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

### 2 — TDD

```
TDD: <ON / OFF>

Do you want to keep it as is or change it?
  [keep / change]
```

**If they choose keep**: move to the next option.

**If they want to change (enable)**: inject the TDD Protocol section into
`AGENTS.md`. Run `/sdd-init` so it detects the test runner and configures
Testing Capabilities. Ensure `wf-orchestrator` is also present (it must be
built whenever `wf-ladder`, `wf-sdd-trigger`, or `wf-tdd` is active).
**Update the footer** to `tdd=yes`.

After enabling, ask about options:

```
TDD enabled. Do you want to configure these options?
3. TDD Mode              <standard / strict>     [current: standard]
4. Coverage targets      <percentage / OFF>      [current: OFF]
5. Visual regression     <ON / OFF>              [current: OFF]
6. Page Object Model     <ON / OFF>              [current: OFF]

Which one do you configure? [3 / 4 / 5 / 6 / none]
```

**If they want to change (disable)**: remove the TDD Protocol section from
`AGENTS.md`. Ask if they want to keep or clean
`openspec/testing-capabilities.yaml`. **Update the footer** to `tdd=no`.
**Update `.wizard-state.json`**: `features.tdd_protocol = false`.
If no other `wf-` protocol remains active (`ladder`, `routing`), also remove `wf-orchestrator`.

---

### 3 — TDD Mode

```
Current mode: <standard / Strict>

Which one do you want to switch to?
  1. Standard TDD Protocol
  2. Strict TDD Mode
```

**If switching to Strict TDD**: write directly to the real sources,
with the exact format of the official `sdd-init` template (confirmed in
`references/init-details.md` — do not delegate to `/sdd-init` for this change:
empirically confirmed that this skill does not rewrite anything if `openspec/`
already exists, and never asks about Strict TDD interactively — it only uses
an existing value or applies its own automatic default).

Save to Engram, with the correct `--type` (`config`, not `convention`):

```bash
engram save "sdd/{project}/testing-capabilities" "## Testing Capabilities

**Strict TDD Mode**: enabled
**Detected**: $(date +%Y-%m-%d)

### Test Runner
- Command: <detected command>
- Framework: <detected framework>

### Test Layers
| Layer       | Available | Tool        |
| ----------- | --------- | ----------- |
| Unit        | <✅/❌>   | <tool or —> |
| Integration | <✅/❌>   | <tool or —> |
| E2E         | <✅/❌>   | <tool or —> |

### Coverage
- Available: <✅/❌>
- Command: <command or —>

### Quality Tools
| Tool         | Available | Command        |
| ------------ | --------- | -------------- |
| Linter       | <✅/❌>   | <command or —> |
| Type checker | <✅/❌>   | <command or —> |
| Formatter    | <✅/❌>   | <command or —> |" \
  --project "{project-name}" --type config
```

Additionally, if the backend is `openspec` or `hybrid`, also write:

```yaml
testing:
  strict_tdd: true
```

If the active agent is Claude Code or Windsurf, also run:

```bash
gentle-ai sync --strict-tdd
```

**If switching to Standard TDD Protocol** (coming from Strict): same
mechanism, with `strict_tdd: false` / `**Strict TDD Mode**: disabled` in
both sources as applicable per backend.

1. If the agent is Claude Code or Windsurf and the global block is still
   `enabled`, inform the user that there is no `--no-strict-tdd` command
   — it must be edited manually:

```
There is no gentle-ai command to disable the global block
(known bug in gentle-ai itself, not this wizard). If you use Claude
Code or Windsurf, edit manually:
  ~/.claude/CLAUDE.md (or ~/.codeium/windsurf/memories/global_rules.md)
Look for the <!-- gentle-ai:strict-tdd-mode --> block and change
"Strict TDD Mode: enabled" to "Strict TDD Mode: disabled".

This is only the informational global block — what sdd-init just
wrote to the real source (Engram and/or openspec/config.yaml, depending on your
backend) is what actually determines that sdd-apply goes back to standard
mode, regardless of what that block says.
```

2. Restore in `AGENTS.md`, under `### 🧪 TDD Protocol (standard)`, the
   "Protocol per change" and "Implementation cycle" subsections — they
   were omitted if the project originally chose Strict TDD.

   **SINGLE SOURCE**: Do NOT copy an embedded block from this file. Read the
   VERBATIM content from `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/tdd/variants/standard.md` (which is the
   `standard` variant of the `tdd` protocol) and insert it as-is. Do not summarize, do not
   paraphrase: without the exact `🧪 TDD PROPOSAL` format and its numbered options, the
   executing agent has no real pause point before writing tests or code.

   Also regenerate the `tdd` protocol packaging (skill `.claude/skills/wf-tdd/`
   and flat `.agents/protocols/tdd.md`) from the single source (Builder B4), so they
   do not get out of sync.

3. **Do not touch** "Playwright Dual-loop" or "wf-sdd-trigger Integration"
   — those two subsections do not depend on the TDD mode
   (they depend on whether the E2E layer is active) and must remain intact
   regardless of which mode is switched to. If you notice they are missing from the current
   `AGENTS.md`, it is a bug in the original `/wf-init` generation (not something
   `/wf-settings` should fix as a side effect) — inform the user instead of
   writing them yourself here.

Confirm:
```
✓ TDD mode changed to: <new mode>
```

**State update**:
```bash
jq '.testing.tdd_mode = "<standard|strict>"' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 4 — Coverage targets

```
Coverage targets: <ON (threshold: N%) / OFF>

Do you want to keep or change?
  [keep / change to <new_threshold>% / disable]
```

**If enabling**: ask for the threshold (same as in `wf-init.md` Phase 4.6) and
add the `coverage.thresholds` block to `vitest.config.ts`. Save in
`openspec/config.yaml` the field `rules.verify.coverage_threshold` (gentle-ai's canonical
field, via Phase 8 step 8.1d — never stamped).

**If disabling**: remove the `coverage.thresholds` block from `vitest.config.ts`
and the `rules.verify.coverage_threshold` field from `openspec/config.yaml` (leave it
unset or `0`).

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

### 5 — Visual regression

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

### 6 — Page Object Model

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

### 7 — wf-sdd-trigger

```
wf-sdd-trigger (this project's own SDD-forcing policy): <ON / OFF>

Do you want to keep or change?
  [keep / change]
```

**If they choose keep**: move to the next option.

**If they want to change (enable)**: set `state.routing_abc = true`, inject
the `wf-sdd-trigger` + `wf-preflight` + PRECHECK section into `AGENTS.md`
(from the `wf-init.md` template), and ensure `wf-orchestrator` is also present
(it must be built whenever `wf-ladder` OR `wf-sdd-trigger` OR `wf-tdd` is active). Run
`phase45.md` to initialize gentle-ai's SDD if it does not exist. **Update the
footer**'s `routing=` token to `yes` (same `sed` pattern as Option 1, targeting
`routing=` instead of `ladder=`).

**If they want to change (disable)**: set `state.routing_abc = false`. Remove
the `wf-sdd-trigger`, `wf-preflight`, and PRECHECK sections from `AGENTS.md`.
**Important**: the PRECHECK lives inside `wf-sdd-trigger` — if it was only
there because of this feature, it does not become orphaned. If `wf-ladder` or
`wf-tdd` standalone is still active, keep `wf-orchestrator` and the remaining
standalone protocol (standalone `wf-ladder` and standalone `wf-tdd` have no
PRECHECK). If none remain active, remove `wf-orchestrator`.
**Update the footer**'s `routing=` token to `no`.

Confirm:
```
✓ wf-sdd-trigger: <enabled / disabled>
✓ .wizard-state.json: features.routing_abc = <yes/no>
✓ AGENTS.md footer updated
```

**State update**:
```bash
jq '.features.routing_abc = <value>' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 8 — SDD persistence backend

```
Current backend: <engram / openspec / hybrid>

Supported migrations:
  engram   → hybrid    (adds git versioning, keeps local memory)
  openspec → hybrid    (adds cross-session memory, keeps versioning)
  hybrid   → engram     (loses git versioning — not recommended)
  hybrid   → openspec    (loses cross-session memory — not recommended)

Do you want to keep or migrate?
  [keep / migrate to <destination>]
```

**If they choose keep**: move to the next option.

> **This is the most delicate migration** — unlike TDD/extras/
> wf-ladder (which are just config), changing the SDD backend can
> mean moving or duplicating real data (already written specs, Engram
> memories).

**If migrating to `hybrid`** (from engram or openspec): this is the recommended
direction with the least risk — nothing is lost, only the other half is added.
Follow the flow already documented in `wf-refresh.md` for this specific
migration.

**If migrating to `engram` or `openspec` from `hybrid`** (losing the other
half): stop and explicitly confirm that the user understands what is
lost, before touching anything:

```
⚠ Migrating from hybrid to <destination> means you will lose:
  <if destination=engram>: the versioned spec history in openspec/ will
    stop being updated — existing files are NOT deleted, but new specs
    will no longer be versioned in git.
  <if destination=openspec>: Engram's cross-session memory will stop being
    consulted for this project — the context the team accumulated there
    is not lost from Engram's binary, but sdd-apply will stop reading it.

Do you confirm you want to continue anyway? [yes / no]
```

**Wait for explicit confirmation.** Only after confirming, apply a **targeted, agent-driven edit**
to the existing `openspec/config.yaml` (never regenerate/overwrite it — see protocol `sdd`,
"Wizard-Allowed Field Edits"): read the real file first, locate whichever field it actually uses to
declare the backend (the exact key name can vary — e.g. `artifact_store`, `backend`, `schema` — do
not assume; gentle-ai's own docs confirm the shape is not fully uniform), change only that leaf
value to the new backend, and preserve `context.*`, `sdd.*`, `notes`, and every other key verbatim.

> **About `strict_tdd` when migrating**: since Engram always saves
> `sdd/{project}/testing-capabilities` regardless of the declared
> backend, **that value is never lost during migration** — it was already in Engram
> before the migration and remains there afterwards. The only thing that changes
> depending on the new backend:
>
> - **Migrating to `openspec` or `hybrid`** (from pure `engram`, where
>   `openspec/` NEVER EXISTED): unlike the TDD mode change in an
>   already existing structure (which is written directly), here it does make sense
>   to ask the user to run `/sdd-init` — because it is a new
>   `openspec/` initialization, not a re-write of something already initialized, and there
>   the real skill does its full work. The Hard Rule of "do not rewrite
>   if it already exists" does not apply to this case because `openspec/` genuinely
>   did not exist before.
> - **Migrating to pure `engram`** (from `openspec` or `hybrid`): no
>   action on `strict_tdd` is needed — Engram already had it. The
>   existing `openspec/config.yaml` can stay as is (it is no longer consulted
>   for SDD, but leaving it does no harm).

Confirm:
```
✓ SDD backend changed to: <new backend>
✓ .wizard-state.json: sdd.backend = <new backend>
✓ strict_tdd: <value> (was already in Engram; <if applicable> also written to
  openspec/config.yaml for the new backend)
```

**State update**:
```bash
jq '.sdd.backend = "<new backend>"' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 9 — CI

```
CI: <ON / OFF>

Do you want to keep or change?
  [keep / change]
```

**If they choose keep**: move to the next option.

**If they want to change (enable)**:

**Case A — release-please standalone is OFF** (no CI active):
Full CI. Ask if they want E2E in CI (sub-option 10).
Set `state.features.ci = true`. Run `phase47-cicd.md` to configure.

**Case B — release-please standalone is ON** (already has conventional
commits + release-please):
You already have release-please standalone active. Enabling full CI
SUBSUMES your current setup:
  - Conventional commits → stays (you already have it)
  - release-please → stays (you already have it)
  - ADDS: Quality Guard + AI review + Security review (optional)
  - ADDS: E2E in CI (optional)

Enable full CI over your current setup? [yes / no]

If yes: set `state.features.ci = true`, `state.release_please = true`
(stays). Run `phase47-cicd.md`. Ask about E2E in CI.

**If they want to change (disable)**:

```
CI is currently active. Do you want to migrate to release-please standalone
(conventional commits + auto-release, without quality guard or AI review)
or disable the entire pipeline? [migrate / disable everything]
```

If they choose `migrate`: set `state.ci = false`, `state.release_please = true`,
inject the release-please standalone configuration.
If they choose `disable everything`: set both to `false`, remove the
CI and release-please sections from `AGENTS.md`.

**Update the footer** according to the new state.

Confirm:
```
✓ CI: <enabled / disabled / migrated to standalone>
✓ .wizard-state.json: features.ci = <yes/no>
✓ AGENTS.md footer updated
```

**State update**:
```bash
jq '.features.ci = <value>' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 10 — AI Reviewer

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
  Provider agnostic: can use Claude, Gemini, Codex, OpenAI, Ollama, etc.
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

1. Claude (Anthropic)
2. Gemini (Google)
3. Codex (OpenAI)
4. OpenAI (GPT)
5. Ollama (local)

Which one? [1-5]
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

### 11 — AI Review Suggestions

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

### 12 — Dedicated Security Review

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
`https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/security-review.<provider>.yml` as
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

### 13 — E2E in CI

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

### 14 — release-please standalone

> Only visible if CI = OFF. If CI is active, release-please is already
> included and this option does not apply.
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
✓ AGENTS.md footer updated
```

**State update**:
```bash
jq '.features.release_please = <value> | .ci.release_please = <value>' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 15 — CD (automatic deploy)

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
fields. Run `phase47-cicd.md` to configure if needed.

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

### 16 — Release strategy

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
If yes: set `state.ci.release_please = true`,
`state.ci.conventional_commits = true`, and `state.cd.trigger = 'tag'`.
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
✓ <if CD ON> .github/workflows/deploy.yml regenerated
✓ <if CD OFF> Instructions for configuring your external CD
```

**State update**:
```bash
jq '.cd.trigger = "<new_trigger>"' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

---

### 17 — Fix Windsurf gentle-ai (conditional, only if Windsurf is active)

**Gate**: Only show this option if Windsurf or Devin is in `state.answers.ides`.

```
Fix Windsurf gentle-ai — Reapply the workaround for gentle-ai's legacy path bug

This reapplies the AGENTS.md rule and .windsurf/workflows/sdd-new.md
in case they were overwritten by a manual "gentle-ai sync".

Do you want to reapply the Windsurf fix now? [yes / no, skip]
```

**If they choose "no, skip"**: move to Phase 4.

**If they choose "yes"**:

1. **Merge AGENTS.md rule** — same as phase45 did:
   - Read the rule from temp-files/AGENTS.md (Gentle AI — Legacy Path Bridge section).
   - Check if it already exists in the project's AGENTS.md.
   - If not present, insert it at the top (after title, before other content).
   - If already present, skip (do not duplicate).

2. **Rewrite .windsurf/workflows/sdd-new.md**:
   - Read `.windsurf/workflows/sdd-new.md` if it exists.
   - If it matches the legacy version (check for "legacy" string or old content), replace it.
   - Write the modern version from temp-files/sdd-new.md.
   - Adapt the backend reference to match `state.sdd.backend`.

Confirm:
```
✓ Windsurf gentle-ai fix reapplied
✓ AGENTS.md rule: in place
✓ .windsurf/workflows/sdd-new.md: updated to modern version
```

---

### 18 — IDEs/CLIs

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

1. **Satellite** — `$WF_RAW/templates/satellites/<ide>.tmpl` → its destination
   (route table in protocol `ides`): `claude-code` → `CLAUDE.md`,
   `vscode-copilot` → `.github/copilot-instructions.md`, `cursor` → `.cursor/rules/project.mdc`,
   `windsurf` → `.windsurf/rules/project.md`, `kiro` → `.kiro/steering/project-context.md`,
   `gemini-cli` → `GEMINI.md`, `antigravity` → `ANTIGRAVITY.md`. Create parent
   directories as needed.
2. **Commands** — every command in the catalog (same list as Builder B7:
   `wf-worktree`, `wf-settings`, `wf-onboard`, plus `wf-ladder` if active) → the IDE's
   command directory
   (`.claude/commands/`, `.cursor/commands/`, `.windsurf/workflows/`, `.kiro/steering/`,
   `.opencode/commands/`, `.github/prompts/`, `.codex/commands/`), applying the per-IDE
   frontmatter (protocol `ides`, routing-table.section.md).
3. **Skills** — the packaged protocol skills → the IDE's native skills directory
   (`.claude/skills/`, `.kiro/skills/`, `.codex/skills/`, `.windsurf/skills/`,
   `.agents/skills/`).
4. **Windsurf fix** — ONLY if the added IDE is Windsurf/Devin: apply the same logic as
   Option 17 (AGENTS.md "Gentle AI — Legacy Path Bridge" rule + `.windsurf/workflows/sdd-new.md`).

Confirm:
```
✓ <IDE> added
✓ Satellite: <path>
✓ Commands: <N> generated in <dir>
✓ Skills: <N> generated in <dir>
<if Windsurf/Devin> ✓ Windsurf fix applied
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
  <if Windsurf/Devin>: - AGENTS.md "Legacy Path Bridge" rule + .windsurf/workflows/sdd-new.md

Confirm deletion? [yes / no]
```

- Delete ONLY the files this wizard generated in the project (satellite, commands, skills).
  Never touch `~/.<ide>/` or gentle-ai's global config.
- If some of the files are already gone, just remove what exists and update the state.
- If the IDE is Windsurf/Devin, also remove the "Legacy Path Bridge" rule from AGENTS.md
  (revert the Option 17 logic) and delete `.windsurf/workflows/sdd-new.md`.

Confirm:
```
✓ <IDE> removed
✓ <satellite path> deleted
✓ <N> commands deleted
✓ <N> skills deleted
<if Windsurf/Devin> ✓ AGENTS.md rule removed
```

**State update**:
```bash
jq '.answers.ides -= ["<ide>"]' .wizard-state.json > .wizard-state.json.tmp && mv .wizard-state.json.tmp .wizard-state.json
```

**If they say something other than `add` or `remove`**: show the current list again and
repeat the question. Do not guess.

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
  ✓ TDD Mode: standard → Strict TDD Mode

Modified files:
  AGENTS.md
  openspec/config.yaml

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
  assume that `AGENTS.md` faithfully reflects what is in
  `openspec/config.yaml`, they may have diverged if someone edited one without
  the other.
- **Each change is confirmed individually** before asking "anything
  else?" — do not silently process several changes and show everything together at the
  end, except in the Phase 5 summary, which is consolidated.
- **Write `strict_tdd` directly with `engram save` (type `config`, not
  `convention`) and by editing `openspec/config.yaml`** — empirically
  confirmed that `/sdd-init` does NOT work for this change: it never asks
  about Strict TDD interactively, and it does not rewrite anything if `openspec/`
  already exists (it only reports and asks before touching, according to its own Hard
Rule). Use `/sdd-init` ONLY when `openspec/` does not yet exist (option
8, migrating to `openspec`/`hybrid` from pure `engram`) — there it is
  a real initialization, not a re-write, and the skill does its full work.
- **SDD backend migration (option 8) is the only one that requires
  a second explicit confirmation** when it implies loss of functionality
  (`hybrid` → `engram`/`openspec`) — the other options do not have that
  risk and do not need double confirmation.
- **Never delete reference files (visual regression snapshots,
  specs with POM)** when disabling an extra without asking first — the
  config disablement does not imply the user wants to lose that
  content.
- **If the user interrupts or says "stop"** at any phase, stop
  completely. Do not auto-complete phases.
- **Do not push** under any circumstances.

---


