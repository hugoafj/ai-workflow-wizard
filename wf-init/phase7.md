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
> **Only when the user explicitly replies "yes"**: mark `phases.phase7.status = done`,
> `phase_pointer = phase8`, and run in bash: `cat "$WF_DIR/phase8.md"`
