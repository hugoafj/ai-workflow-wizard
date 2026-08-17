# 5 CRITICAL ISSUES — Code Review + Fixes

---

## ISSUE #1: A-01 Loop Infinito (phase5 ↔ phase47-cicd)

**Severity**: 🔴 CRITICAL  
**Impact**: Greenfield projects with CI/CD features hang in infinite loop  
**Files**: `wf-init/phase5.md`, `wf-init/phase47-cicd.md`

### Current Code — PROBLEM

#### wf-init/phase5.md (lines 30-49)
```bash
# Compute the next phase based on ALREADY SELECTED features:
if [ "$(jq -r '.features.routing_abc // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.tdd_protocol // false' .wizard-state.json)" = "true" ]; then
  NEXT="phase45"
elif [ "$(jq -r '.features.ci // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.cd // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.release_please // false' .wizard-state.json)" = "true" ]; then
  NEXT="phase47-cicd"  # ← Routes back to phase47-cicd
else
  NEXT="phase6a-agents"
fi
```

#### wf-init/phase47-cicd.md (line 316)
```bash
wf_phase_done phase47-cicd phase5  # ← UNCONDITIONALLY returns to phase5
echo "ℹ Next phase: phase5"
cat "$WF_DIR/phase5.md"
```

### The Loop Scenario
```
Project with ci=true, tdd_protocol=false, routing_abc=false:
  phase4 → phase5 (NEXT=phase47-cicd)
  phase5 → phase47-cicd (because ci=true)
  phase47-cicd → phase5 (unconditional line 316) ← INFINITE LOOP
  phase5 → phase47-cicd (because ci=true still active)
  ...
```

### Fix Suggested

**Solution**: Make phase47-cicd check if it's already complete before returning to phase5.

#### File: wf-init/phase47-cicd.md — CHANGE line 316

**Current**:
```bash
wf_phase_done phase47-cicd phase5
echo "ℹ Next phase: phase5"
cat "$WF_DIR/phase5.md"
```

**Fixed**:
```bash
# After phase47-cicd is complete, check what was already done in this session
# If phase5 is already done, don't loop back. Instead, go directly to phase6a-agents.
PHASE5_DONE=$(jq -r '.phases.phase5.status // "not-started"' .wizard-state.json)

if [ "$PHASE5_DONE" = "done" ]; then
  # phase5 already complete; skip to Builder
  NEXT="phase6a-agents"
  echo "ℹ Phase 5 already completed; moving to Builder"
else
  # phase5 not yet done; send user back to collect answers
  NEXT="phase5"
  echo "ℹ Back to Phase 5 for project details"
fi

wf_phase_done phase47-cicd "$NEXT"
echo "ℹ Next phase: $NEXT"
cat "$WF_DIR/$NEXT.md"
```

---

## ISSUE #2: A-02 Contradictory Prose vs Bash Routing

**Severity**: 🟠 HIGH  
**Impact**: Confusing behavior; conditional logic moved but execution order unclear  
**Files**: `wf-init/phase4.md`

### Current Code — PROBLEM

#### wf-init/phase4.md (lines 33-52)
```bash
> **Persistence**: ... Mark `wf_phase_done phase4 phase5`.
> Always route to Phase 5 to collect project answers (including project_name) before any conditional phases:
> ```bash
> echo "phase5"
> ```

# THEN LATER, the bash block:
if [ "$(jq -r '.features.routing_abc // false' .wizard-state.json)" = "true" ] || ...
  NEXT="phase45"
elif [ ... '.features.ci' ... ] = "true" ]; then
  NEXT="phase47-cicd"
else
  NEXT="phase5"  # ← Can route back to phase5, contradicting prose
fi
wf_phase_done phase4 "$NEXT"
```

### The Issue
- **Prose** says: "Always route to Phase 5"
- **Bash** says: Conditionally route to phase45, phase47-cicd, or phase5
- They contradict each other

### Fix Suggested

**Solution**: Make prose match bash (accept conditional routing).

#### File: wf-init/phase4.md — CHANGE lines 33-35

**Current**:
```bash
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `discovery.conventions` (the detected/corrected conventions from reverse engineering). Mark `wf_phase_done phase4 phase5`.
> Always route to Phase 5 to collect project answers (including project_name) before any conditional phases:
> ```bash
> echo "phase5"
> ```
```

**Fixed**:
```bash
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `discovery.conventions` (the detected/corrected conventions from reverse engineering). Mark `wf_phase_done phase4 <next>`.
> Compute the next phase based on ALREADY SELECTED features. If any have been activated, route to the relevant conditional phase; otherwise phase5:
> ```bash
> if [ "$(jq -r '.features.routing_abc // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.tdd_protocol // false' .wizard-state.json)" = "true" ]; then
>   echo "phase45"
> elif [ "$(jq -r '.features.ci // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.cd // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.release_please // false' .wizard-state.json)" = "true" ]; then
>   echo "phase47-cicd"
> else
>   echo "phase5"
> fi
> ```
```

---

## ISSUE #3: A-03 {project} Substituted as Literal "null"

**Severity**: 🔴 CRITICAL  
**Impact**: Generated `.windsurf/workflows/sdd-new.md` contains literal `{project}` token  
**Files**: `wf-init/phase45.md` (lines 257-273)

### Current Code — PROBLEM

#### wf-init/phase45.md (lines 257-273)
```bash
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
if echo "$IDES" | grep -q "windsurf"; then
  SDD_BACKEND=$(jq -r '.sdd.backend // "hybrid"' .wizard-state.json)
  PROJECT_NAME=$(jq -r '.answers.project_name' .wizard-state.json)  # ← Reads project_name
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
  sed -i.bak "s|{project}|$PROJECT_NAME|g" .windsurf/workflows/sdd-new.md  # ← Substitutes
  rm -f .windsurf/workflows/sdd-new.md.bak
fi
```

### The Issue
- **phase45 runs BEFORE phase5** (when routing_abc OR tdd_protocol is true)
- **phase5 collects `.answers.project_name`**
- By the time phase45 runs, `.answers.project_name` is still **null** or **not set**
- Result: `sed` substitutes `{project}` with empty string or "null"

### Fix Suggested

**Solution A** (Recommended): Defer Windsurf file generation to AFTER phase5

#### File: wf-init/phase45.md — COMMENT OUT the Windsurf generation block

**Current** (lines 257-273):
```bash
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
if echo "$IDES" | grep -q "windsurf"; then
  # ... entire block
fi
```

**Fixed**:
```bash
# NOTE: Windsurf workflow generation is deferred to phase5 (AFTER project_name is collected)
# Do NOT generate .windsurf/workflows/sdd-new.md here.
#
# IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
# if echo "$IDES" | grep -q "windsurf"; then
#   # ... deferred
# fi
```

#### File: wf-init/phase5.md — ADD Windsurf generation AFTER project collection

**Add this BEFORE the `Mark wf_phase_done phase5 $NEXT` line** (around line 28):

```bash
### Windsurf workflow setup (if applicable)

If Windsurf is active, generate `.windsurf/workflows/sdd-new.md` with the correct `{project}` substitution:

```bash
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
if echo "$IDES" | grep -q "windsurf"; then
  SDD_BACKEND=$(jq -r '.sdd.backend // "hybrid"' .wizard-state.json)
  PROJECT_NAME=$(jq -r '.answers.project_name' .wizard-state.json)  # ← NOW project_name is set
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
```

---

## ISSUE #4: B-01 New Features Never Asked (migrate_state trap)

**Severity**: 🟠 HIGH  
**Impact**: New optional features in future wizard versions never prompt user  
**Files**: `wf-init/lib/refresher.md` (lines 275-286)

### Current Code — PROBLEM

#### wf-init/lib/refresher.md (lines 275-286)
```bash
migrate_state() {
  local CURRENT="$1"
  local TARGET="$2"

  if ! version_lt "$CURRENT" "$TARGET"; then
    echo "  No migration needed: $CURRENT already >= $TARGET"
    return 0
  fi

  echo "  Upgrading state from $CURRENT to $TARGET..."
  
  # Ensure schema v3 required fields exist (idempotent: //= creates only if missing).
  # Known features get false defaults so they are never re-asked if they already exist.
  # NEW features (in future versions) remain absent, so Builder will ask about them.
  _apply_jq_filter '
    .schema_version = 3 |
    .wizard_version = "'"$TARGET"'" |
    .build_plan //= {} |
    .build_plan.managed_paths //= [] |
    .build_plan.generated_files //= [] |
    .build_plan.approval //= {} |
    .features //= {} |
    .features.routing_abc //= false |   ← PROBLEM: Sets ALL known features to false
    .features.decision_ladder //= false |
    .features.tdd_protocol //= false |
    .features.ci //= false |
    .features.cd //= false |
    .features.release_please //= false |
    .ci //= {} |
    .ci.e2e_in_ci //= false |
    .ci.auto_improve //= true |
    .ci.inline_suggestions //= true
  '

  echo "  ✓ State upgraded from $CURRENT to $TARGET"
}
```

### The Issue
- `//=` (alternative operator) **creates a field if missing and sets it to the right side**
- Comment says "NEW features remain absent so Builder will ask about them"
- **BUT** this only works if NEW features are NOT in the jq filter
- Once a feature is in this filter, it's **always present** with value `false`
- Builder only asks about features **not in `.features` yet**
- Result: New features added in future wizard versions are **never asked because they're pre-set to false**

### Fix Suggested

**Solution**: Don't set feature defaults in migrate_state. Let only existing features be preserved as-is.

#### File: wf-init/lib/refresher.md — CHANGE lines 275-286

**Current**:
```bash
  _apply_jq_filter '
    .schema_version = 3 |
    .wizard_version = "'"$TARGET"'" |
    .build_plan //= {} |
    .build_plan.managed_paths //= [] |
    .build_plan.generated_files //= [] |
    .build_plan.approval //= {} |
    .features //= {} |
    .features.routing_abc //= false |
    .features.decision_ladder //= false |
    .features.tdd_protocol //= false |
    .features.ci //= false |
    .features.cd //= false |
    .features.release_please //= false |
    .ci //= {} |
    .ci.e2e_in_ci //= false |
    .ci.auto_improve //= true |
    .ci.inline_suggestions //= true
  '
```

**Fixed**:
```bash
  _apply_jq_filter '
    .schema_version = 3 |
    .wizard_version = "'"$TARGET"'" |
    .build_plan //= {} |
    .build_plan.managed_paths //= [] |
    .build_plan.generated_files //= [] |
    .build_plan.approval //= {} |
    .features //= {} |
    .ci //= {} |
    .ci.e2e_in_ci //= false |
    .ci.auto_improve //= true |
    .ci.inline_suggestions //= true
  '
  
  # DO NOT set default values for known features here.
  # The comment was correct: new features should remain absent so Builder asks about them.
  # For EXISTING features, use jq to preserve them if they're already present, don't create them.
  # This way, features only added when user explicitly chooses them in Builder.
```

---

## ISSUE #5: B-02 R-1/R0 Labeling Contradicts Implementation

**Severity**: 🟠 HIGH  
**Impact**: Documentation doesn't match code; confusing terminology  
**Files**: `AI_DEV_WORKFLOW.md` (lines 707, 760-761)

### Current Code — PROBLEM

#### AI_DEV_WORKFLOW.md (line 707)
```markdown
- **Phase R-1**: Update global commands (`wf-init`, `wf-refresh`, `wf-cleanup`) if outdated
```

#### AI_DEV_WORKFLOW.md (lines 760-761)
```markdown
- **Phase R-1 · Pre-flight state checks**: Validates `.wizard-state.json` exists and contains minimal required structure.
```

### The Issue
- **Line 707** says R-1 = "Update global commands"
- **Line 760-761** says R-1 = "Pre-flight state checks"
- **Actual implementation** (refresher.md) R-1 = fetch wizard version + check if outdated
- **Actual implementation** R0 = validate state + detect IDEs
- **Documentation contradicts itself** (line 707 vs 760-761)

### Fix Suggested

**Solution**: Align documentation with actual implementation

#### File: AI_DEV_WORKFLOW.md — CHANGE lines 707-710

**Current**:
```markdown
- **Phase R-1**: Update global commands (`wf-init`, `wf-refresh`, `wf-cleanup`) if outdated
- **Phase R0**: Validate `.wizard-state.json` and detect active IDEs
- **Phase R1**: Re-discover project (stack, node engine, etc.) and detect drift
- **Phase R2**: Migrate state schema and ask about new optional features
```

**Fixed**:
```markdown
- **Phase R-1** (Global): Fetch wizard version from GitHub; skip refresh if already up-to-date
- **Phase R0** (Validate): Validate `.wizard-state.json` structure and detect active IDEs
- **Phase R1** (Discover): Re-discover project (stack, node engine, etc.) and detect drift
- **Phase R2** (Migrate): Migrate state schema; ask about new optional features
```

#### File: AI_DEV_WORKFLOW.md — CHANGE lines 760-761

**Current**:
```markdown
- **Phase R-1 · Pre-flight state checks**: Validates `.wizard-state.json` exists and contains minimal required structure.
```

**Fixed**:
```markdown
- **Phase R-1 · Global version check**: Fetches wizard version from remote; exits early if already up-to-date.
- **Phase R0 · Pre-flight state checks**: Validates `.wizard-state.json` exists and contains minimal required structure; detects active IDEs.
```

---

## Summary Table

| Issue | File | Lines | Current | Fix |
|-------|------|-------|---------|-----|
| **A-01** Loop | phase47-cicd.md | 316 | Unconditional `phase5` | Check if phase5 done; else go to phase6a-agents |
| **A-02** Prose vs Bash | phase4.md | 33-35 | Contradictory | Update prose to match conditional bash logic |
| **A-03** {project} null | phase45.md → phase5.md | 257-273 → 28 | Generate in phase45 (too early) | Defer to phase5 (after project_name collected) |
| **B-01** Features trap | refresher.md | 275-286 | Set all features to false | Remove feature defaults; let Builder ask about new ones |
| **B-02** Labeling | AI_DEV_WORKFLOW.md | 707, 760-761 | Contradictory labels | Align with actual R-1/R0 behavior |

---

**Total Changes**: ~25 lines across 5 files  
**Estimated Time**: 30 min  
**Blocker Status**: All 5 must be fixed before merge
