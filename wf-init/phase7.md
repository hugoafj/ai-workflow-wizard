## PHASE 7 — Human review gate

> The review reads artifacts from the **STAGING on disk**
> (`.wizard-staging/`), NOT from the model's memory. This way what the user approves is
> exactly what will be written.

### Step 7.1 — Show the staging

Read from disk and show the user **everything that will be written**, before touching the
project:

```bash
STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' .wizard-state.json)
echo "=== AGENTS.md (full content) ==="; cat "$STAGING/AGENTS.md"
echo "=== Staging files ==="; find "$STAGING" -type f | sort
```

Present the summary:

```
REVIEW GATE — Review before I write any files
===========================================================

AGENTS.md (thin router, full content shown above)

Files to be created (from .wizard-staging/):
  AGENTS.md
  CLAUDE.md                        (if applicable — only when claude-code is active)
  .agents/protocols/<...>.md        (packaged protocols, flat file)
  .claude/skills/<...>/SKILL.md      (packaged protocol skills — native per IDE + .agents/skills/ universal)
<list based on confirmed IDEs: satellites and commands>
  .git/hooks/post-commit

Changes to .gitignore:
  Exceptions will be added so that satellites are versioned:
    !.cursor/  (if applicable)
    !.windsurf/  (if applicable)
    !.kiro/  (if applicable)
    !.github/copilot-instructions.md  (if applicable)
    .wf-status          (ignored — it's local)
    .wizard-state.json  (ignored — it's local)
    .wizard-staging/    (ignored — it's temporary)
```

Side effects that Phase 8 will apply AFTER your approval — visible now so the approval
covers them (field report B14: installs were invisible at review time):

```
SIDE EFFECTS in Phase 8 (installs + package.json changes):
<if state.ci.conventional_commits == true>:
  - npx husky init → creates .husky/, adds "prepare" script to package.json,
    installs commitlint; replaces Husky's factory pre-commit with an inert hook.
</if>
<if unit/integration layer active>:
  - npm install: vitest, @testing-library/*, jsdom, @vitest/ui, @vitest/coverage-v8
    (+ @vitejs/plugin-react on React stacks).
</if>
<if e2e layer active>:
  - npm install: @playwright/test; downloads Chromium via npx playwright install --with-deps.
</if>
<if any testing layer active>:
  - package.json scripts added: test, test:ui, test:coverage (+ test:e2e, test:e2e:ui, test:e2e:report).
</if>
Approving this gate approves these installs too.
```

Include only the lines whose condition matches `.wizard-state.json` — if none match, skip the block entirely.

If custom content was migrated from a previous AGENTS.md:

```
CUSTOM CONTENT — Automatically protected
=========================================================

The following sections from your previous AGENTS.md are wrapped 
with protection markers so /wf-refresh will never overwrite them:

<!-- WF: DO NOT REGENERATE -->
## Your Custom Section Name
[content preview...]
<!-- /WF: DO NOT REGENERATE -->

The markers mean: even when you run /wf-refresh in the future,
these sections will remain exactly as you wrote them.

Do you approve? [yes / edit first: <describe the change>]
```

If no custom content: skip this section.

**PAUSE — Wait for explicit approval.**

If the user asks to edit something: adjust the data in `.wizard-state.json`, re-run the
Builder (Phase 6) to regenerate the STAGING, and show the review again. Never edit the
staging manually bypassing the state — the state is the source of truth.

---
> **⛔ STOP HERE — DO NOT write any files outside staging yet.**
> Tell the user exactly this: *"Review complete. Reply **yes** to approve and write all files, or **edit first: [description]** to adjust something."*

> **Only when the user explicitly replies "yes"**: run the block below to advance the
> state, then read the next phase: `cat "$WF_DIR/phase8.md"`. Do NOT read phase8
> before the approval — it writes to the project.
```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"
wf_state_init

# Validate state before phase transition
jq -e '.build_plan.generated_files != null and .build_plan.managed_paths != null' .wizard-state.json || { echo "FAIL: build_plan validation failed"; exit 1; }

wf_phase_done phase7 phase8
cat "$WF_DIR/phase8.md"
```
