### Step 0.4 — Check health status with gentle-ai doctor

```bash
gentle-ai doctor
```

Evaluate the output:

**Critical checks** (if any fails with `[fail]`, the wizard CANNOT continue):
- `tool:gentle-ai` → must be `ok`
- `tool:engram` → must be `ok`
- `state:json` → must be `ok` with at least one agent configured

**Important checks** (if they fail, warn but don't block):
- `engram:reachable` → if it fails, Engram is not running. Inform that the agent will start it on-demand. Not blocking for the wizard.
- `disk:space` → if less than 500MB, warn but don't block.

**Cosmetic warnings** (ignore them):
- `[!!] degraded` due to PATH duplicates → does not affect functionality.

If there are `[fail]` critical checks:

```
gentle-ai doctor reports issues blocking the workflow:

  [fail] <check>: <description>

Suggested remedies:
  <Copy the "Remedy" column from the doctor output>

Please resolve these issues and run /wf-init again.
The wizard cannot continue in this state.
```

If everything is `ok` or non-critical `[!!]`, show a clean summary:

```
✓ gentle-ai doctor — OK
  Version: <version>
  Configured agents: <list of agents from state:json>
  Engram: <reachable / not reachable — will be started on-demand>
```

**Persist doctor results to state:**

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Extract version from doctor output (first line like "gentle-ai v0.8.18-beta.1")
DOCTOR_VERSION=$(echo "$DOCTOR_OUTPUT" | head -1 | sed -E 's/.*v?([0-9]+\.[0-9]+\.[0-9]+(-[a-z0-9.]+)?).*/\1/')

# Detect if gentle-ai is installed (doctor returns 0 if OK)
if echo "$DOCTOR_OUTPUT" | grep -q "tool:gentle-ai.*ok"; then
  INSTALLED=true
else
  INSTALLED=false
fi

# Detect OS from uname (for path/binaries decisions)
case "$(uname -s)" in
  Darwin) OS="darwin" ;;
  Linux)  OS="linux" ;;
  *)      OS="unknown" ;;
esac

wf_state_set '.gentle_ai.doctor' '"ok"'
wf_state_set '.gentle_ai.version' "\"$DOCTOR_VERSION\""
wf_state_set '.gentle_ai.install_choice' '"wizard"'
wf_state_set '.gentle_ai.installed' $INSTALLED
wf_state_set '.gentle_ai.os' "\"$OS\""
```

---

### Step 0.4b — Check gentle-ai sync freshness (hard stop, non-ignorable)

> **Why this step exists**: gentle-ai's own native SDD orchestrator/routing content (installed
> per adapter — e.g. `~/.codeium/windsurf/memories/global_rules.md` for Windsurf/Devin) is only
> updated by `gentle-ai sync`. If the user upgraded the `gentle-ai` binary but never ran `sync`,
> that native content can be stale relative to the current binary — a documented, reproducible
> source of agents skipping or inventing SDD phases (a stale orchestrator prompt). This check is
> NOT optional and its result is NOT something the agent may silently decide to ignore.

First, capture the dry-run output to a variable:

```bash
# Run sync dry-run, capturing both stdout and stderr
if ! SYNC_OUTPUT=$(gentle-ai sync --dry-run 2>&1); then
  SYNC_EXIT=$?
  echo "⚠ gentle-ai sync --dry-run failed (exit $SYNC_EXIT):"
  echo "$SYNC_OUTPUT"
  echo ""
  echo "Cannot determine sync status. What do you want to do?"
  echo "  [retry]         — run gentle-ai sync --dry-run again"
  echo "  [skip check]    — continue without sync verification (not recommended)"
  echo "  [abort]         — stop wizard, fix gentle-ai first"
  read -r SYNC_CHOICE
  case "$SYNC_CHOICE" in
    retry)
      # Re-run the sync check (user must re-trigger this step)
      echo "Please re-run the sync check step."
      exit 1
      ;;
    skip*)
      echo "ℹ Skipping sync check, continuing anyway"
      wf_state_set '.gentle_ai.sync_stale_accepted' true
      ;;
    *)
      echo "Aborted."
      exit 1
      ;;
  esac
else
  # Classify output: "Apply steps: N" where N > 0 = REAL drift (gentle-ai doesn't list files in dry-run)
  # "Apply steps: 0" / "Nothing to do" / "Up to date" = no drift
  # Anything else / ambiguous = show verbatim and ask
  if echo "$SYNC_OUTPUT" | grep -qE 'Apply steps: [1-9][0-9]*'; then
    SYNC_HAS_DRIFT=true
  elif echo "$SYNC_OUTPUT" | grep -qiE 'Apply steps: 0|Nothing to do|Up to date|up.to.date|no changes|no pending'; then
    SYNC_HAS_DRIFT=false
  else
    SYNC_HAS_DRIFT="ambiguous"
  fi
fi
```

**If user chose "sync now"**: run `gentle-ai sync`, show its output, then **re-run `gentle-ai sync --dry-run` to confirm it now reports no pending changes** before continuing to Step 0.5.

Classify the output BEFORE deciding it reports drift (field report B6): static plan metadata —
step counters like "Apply steps: N" or plan summaries that print identically on every run,
even right after a real sync of hundreds of files — is NOT drift. A drift signal is an explicit
statement about specific files that WOULD change/write/update now. Only such a listing counts
as pending changes; if the output is ambiguous, show it verbatim to the user and ask instead
of deciding either way.

**If the output reports NO pending changes** (sync is current): continue silently to Step 0.5, no
message needed.

**If the output reports ANY pending changes**: this is a **hard stop**. Present the FULL output to
the user verbatim (do not summarize or paraphrase what would change), then STOP and wait — the
agent must NOT decide on the user's behalf to continue or to sync:

```
⚠ gentle-ai's native content for your IDE(s) is out of sync with the installed gentle-ai version.

<paste $SYNC_OUTPUT here, verbatim>

This matters because gentle-ai's own SDD orchestrator/routing rules — which this wizard's own
protocols (wf-orchestrator, wf-sdd-trigger, wf-ladder, wf-tdd) explicitly defer to for all
routing and delegation — may be stale until you sync. Continuing with stale native content is a
known source of the agent skipping or inventing SDD phases.

What do you want to do?
  [sync now]         — run `gentle-ai sync` before continuing this wizard.
  [continue anyway]  — proceed without syncing. You explicitly accept the risk described above.
```

**PAUSE — wait for the user's explicit response.** Do not infer a choice, do not default to
either option, and do not continue silently under any circumstance.

- If `sync now`: run `gentle-ai sync`, show its output, then **re-run `gentle-ai sync --dry-run` to confirm it now reports no pending changes** before continuing to Step 0.5.
**If the output is ambiguous** (could not classify): present the FULL output verbatim and ask:

```
⚠ gentle-ai sync --dry-run output could not be automatically classified:

<paste $SYNC_OUTPUT here, verbatim>

Does this indicate pending changes that should be synced?
  [yes, sync now]    — run `gentle-ai sync` before continuing
  [no, continue]     — proceed without syncing (record as sync_stale_accepted=true)
```

---

### Step 0.5 — Confirm active agents

Show the list of agents that `gentle-ai doctor` / `gentle-ai status` reported as configured. Ask:

```
AI agents detected and configured with gentle-ai:
  <list>

Are these the IDEs/CLIs you will use in this project? [yes / add/remove: <name>]

The project satellites (per-IDE context files) will be generated
in Phase 6b only for the agents you confirm here.
```

**Wait for user response.** Save the final agent list in `state.answers.ides` (used by the Builder to generate satellites).

**Persist confirmed IDEs to state:**

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# CONFIRMED_IDES_ARRAY should be a JSON array like '["opencode","windsurf"]'
wf_state_set '.answers.ides' "$CONFIRMED_IDES_ARRAY"
```

---

### ✓ PHASE 0 COMPLETED

```
Prerequisite verified:
  gentle-ai: v<version> ✓
  Engram: <status> ✓
  Configured agents: <list> ✓

Continuing with project discovery...
```

**PAUSE — The user must respond "continue" or "yes" to proceed to Phase 0c (feature selection).**

---
> **⛔ STOP HERE — do not execute anything else.**
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `gentle_ai.doctor`, `gentle_ai.version`, `gentle_ai.install_choice`, `gentle_ai.sync_stale_accepted`, `answers.ides` (final confirmed agent list). Mark `wf_phase_done phase0b phase0c`.
> **Validation**: before `wf_phase_done`, verify critical fields are not null:
> ```bash
> jq -e '.gentle_ai.doctor != null and .gentle_ai.version != null and .answers.ides | type == "array"' .wizard-state.json || { echo "FAIL: state validation failed"; exit 1; }
> ```
> Tell the user: *"Phase 0 completed. Reply **continue** to choose which features to configure."*
> Wait for the response. Only when confirmed, run in bash:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Validate state before phase transition (phase-aware validation)
wf_phase_done phase0b phase0c
cat "$WF_DIR/phase0c.md"
```
