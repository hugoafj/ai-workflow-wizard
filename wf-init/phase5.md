## PHASE 5 — Minimum project questions

> The features WERE ALREADY SELECTED in Phase 0c. Here we only ask
> project details that don't depend on the features.

### Question 1 — Project name (if not obvious from package.json)

### [USER MESSAGE]
```
What is this project called? (for AGENTS.md)
```

### ⏸ PAUSE — Waiting for user response...

### Question 2 — Exact stack (if there is ambiguity)

### [USER MESSAGE]
```
Detected: <stack>. Correct versions? For example: React 19.2, Vite 8.0, TypeScript 6.0, Tailwind 4.0
```

### ⏸ PAUSE — Waiting for user response...

### Question 3 — Critical constraints (only if the project has something non-standard)

### [USER MESSAGE]
```
Is there any critical constraint the agent must NEVER violate in this project?
Examples: "don't install dependencies without approval", "never touch src/legacy/",
"the main branch is protected".
[none / <brief description>]
```

### ⏸ PAUSE — Waiting for user response...

### Persistence

> **📝 PERSISTENCE CHECKLIST** (execute during this phase, before STOP):
> - `wf_state_set '.answers.project_name' '"<name>"'`
> - `wf_state_set '.answers.stack_versions' '"<versions>"'`
> - `wf_state_set '.answers.critical_constraints' '["<constraint1>", ...]'`
> - `wf_state_set '.wf_dir' '"/tmp/wf-init-phases"'`

**Also persist WF_DIR for resumption (fix #11):**

### [WIZARD ACTION]
```bash
wf_state_set '.wf_dir' '"/tmp/wf-init-phases"'
```

Phase 5 always advances to `phase6a-agents`. Every conditional phase (4.5, 4.6,
4.6b, 4.7) already ran BEFORE Phase 5 in the wizard flow, so there is no routing
decision left to make here — routing back to a completed conditional phase would
re-run it (regression: phase5↔phase45 / phase5↔phase47-cicd loop).

---

### Windsurf workflow setup (if applicable)

If Windsurf is active, generate `.windsurf/workflows/sdd-new.md` now that project_name is available:

### [WIZARD ACTION]
```bash
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
if echo "$IDES" | grep -q "windsurf"; then
  SDD_BACKEND=$(jq -r '.sdd.backend // "hybrid"' .wizard-state.json)
  PROJECT_NAME=$(jq -r '.answers.project_name' .wizard-state.json)
  WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
  SDD_PATH="$SDD_BACKEND"
  [ "$SDD_BACKEND" = "hybrid" ] && SDD_PATH="openspec"
  mkdir -p .windsurf/workflows
  cp "$WF_DIR/temp-files/sdd-new.md" .windsurf/workflows/sdd-new.md
  if [ "$SDD_BACKEND" = "engram" ]; then
    sed -i.bak "s|{{sdd.backend}}/changes/<name>/proposal.md|Engram memory:|g" .windsurf/workflows/sdd-new.md
  else
    sed -i.bak "s|{{sdd.backend}}/changes/|$SDD_PATH/changes/|g" .windsurf/workflows/sdd-new.md
  fi
  sed -i.bak "s/{{sdd.backend}}/$SDD_BACKEND/g" .windsurf/workflows/sdd-new.md
  sed -i.bak "s|{project}|$PROJECT_NAME|g" .windsurf/workflows/sdd-new.md
  rm -f .windsurf/workflows/sdd-new.md.bak
fi
```

---

═══════════════════════════════════════════════════════
⛔ PHASE 5 COMPLETE — Ready for Phase 6a-agents
⏸ PAUSE — Waiting for user to confirm "continue"

### [USER MESSAGE]
Questions completed. Reply **continue** so I can assemble the artifacts (Builder → staging on disk, not in memory).

### [WIZARD ACTION]
When user confirms, run EXACTLY:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Persist WF_DIR for resumption
wf_state_set '.wf_dir' '"/tmp/wf-init-phases"'

# Validate state before phase transition (phase-aware validation)
wf_phase_done phase5 phase6a-agents
cat "$WF_DIR/phase6a-agents.md"
```
