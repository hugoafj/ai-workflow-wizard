### Step 0.4 — Check health status with gentle-ai doctor

### [WIZARD ACTION]
```bash
# Capture doctor output for evaluation and persistence
DOCTOR_OUTPUT=$(gentle-ai doctor)
echo "$DOCTOR_OUTPUT"
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

### [USER MESSAGE]
```
gentle-ai doctor reports issues blocking the workflow:

  [fail] <check>: <description>

Suggested remedies:
  <Copy the "Remedy" column from the doctor output>

Please resolve these issues and run /wf-init again.
The wizard cannot continue in this state.
```

### ⏸ PAUSE — Wizard cannot continue, user must fix issues first...

If everything is `ok` or non-critical `[!!]`, show a clean summary:

### [USER MESSAGE]
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
  INSTALLED="true"
else
  INSTALLED="false"
fi

# Detect OS from uname (for path/binaries decisions)
case "$(uname -s)" in
  Darwin) OS="darwin" ;;
  Linux)  OS="linux" ;;
  *)      OS="unknown" ;;
esac

# Persist to state using wf_state_set (jq --arg handles all escaping safely)
wf_state_set '.gentle_ai.doctor' "ok"
wf_state_set '.gentle_ai.version' "$DOCTOR_VERSION"
wf_state_set '.gentle_ai.install_choice' "wizard"
wf_state_set '.gentle_ai.installed' "$INSTALLED"
wf_state_set '.gentle_ai.os' "$OS"
```

---

### Step 0.4b: Check installed asset freshness (hard stop, non-ignorable)

> **Why this step exists**: the ODD orchestrator content gentle-ai installs for each IDE
> (e.g. `~/.codeium/windsurf/memories/global_rules.md` for Windsurf/Devin) is only updated by
> `gentle-ai sync`. If the user upgraded the `gentle-ai` binary but never ran `sync`, the ODD
> orchestrator content may be stale relative to the current binary, a documented source of agents
> skipping or inventing workflow phases. This check is NOT optional and its result is NOT something
> the agent may silently decide to ignore.

Read the asset check from `gentle-ai doctor` (read-only):

### [WIZARD ACTION]
```bash
# installed:asset_version compares the assets' recorded binary version with the running binary.
# "[ok]" = current. "[!!]" = stale, and its remedy line says to run gentle-ai sync.
DOCTOR_OUTPUT=$(gentle-ai doctor 2>&1)
ASSET_LINE=$(echo "$DOCTOR_OUTPUT" | grep -E 'installed:asset_version' | head -1)

case "$ASSET_LINE" in
  *"[ok]"*) ASSET_STATUS="current" ;;
  # A [!!] line, a missing line, or any other marker is NOT current: hard stop below.
  *)        ASSET_STATUS="stale_or_unknown" ;;
esac
echo "ASSET_STATUS=$ASSET_STATUS"
```

`gentle-ai sync --dry-run` is NOT used for this decision: its "Apply steps: N" counter is static plan
metadata that prints the same value on every run, even right after a successful sync (field report B6),
so it cannot prove freshness. Only the `[ok]` marker on the `installed:asset_version` line counts as
current.

**If the line is `[ok]`**: continue silently to Step 0.5, no message needed.

**If the line is anything else** (a `[!!]` warning, a missing line, or an unrecognized marker): this is a
**hard stop**. Present the line verbatim (or the full doctor output when the line is missing), then STOP
and wait. The agent must NOT decide on the user's behalf to continue or to sync:

### [USER MESSAGE]
```
⚠ gentle-ai reports that the installed assets for your IDE(s) are not current with the running binary:

<paste the installed:asset_version line from gentle-ai doctor, verbatim>

This matters because the ODD orchestrator content installed for your IDE(s) may be stale until you sync.
Continuing with stale native content is a known source of the agent skipping or inventing
workflow phases.

What do you want to do?
  [sync now]         — run `gentle-ai sync` before continuing this wizard.
  [continue anyway]  — proceed without syncing. You explicitly accept the risk described above.
```

### ⏸ PAUSE — wait for the user's explicit response. Do not infer a choice, do not default to either option, and do not continue silently under any circumstance.

### [WIZARD ACTION]
- If `sync now`: run `gentle-ai sync`, show its output, then **re-run `gentle-ai doctor` to confirm the `installed:asset_version` line is `[ok]`** before continuing to Step 0.5. If it is still not `[ok]`, present this hard stop again.
- If `continue anyway`: run `wf_state_set '.gentle_ai.sync_stale_accepted' true`, then continue to Step 0.5.

---

### Step 0.5 — Confirm active agents

Show the list of agents that `gentle-ai doctor` / `gentle-ai status` reported as configured. Ask:

### [USER MESSAGE]
```
AI agents detected and configured with gentle-ai:
  <list>

Are these the IDEs/CLIs you will use in this project? [yes / add/remove: <name>]

The project satellites (per-IDE context files) will be generated
in Phase 6b only for the agents you confirm here.
```

### ⏸ PAUSE — Waiting for user response...

### [WIZARD ACTION]
Save the final agent list in `state.answers.ides` (used by the Builder to generate satellites).

**Persist confirmed IDEs to state:**

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# CONFIRMED_IDES_ARRAY should be a JSON array like '["opencode","windsurf"]'
wf_state_set '.answers.ides' "$CONFIRMED_IDES_ARRAY"
```

---

### ✓ PHASE 0 COMPLETED

### [USER MESSAGE]
```
Prerequisite verified:
  gentle-ai: v<version> ✓
  Engram: <status> ✓
  Configured agents: <list> ✓

Continuing with project discovery...
```

### ⏸ PAUSE — The user must respond "continue" or "yes" to proceed to Phase 0c (feature selection).

> **📝 PERSISTENCE** (contract `wf-init/lib/state.md`): use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `gentle_ai.doctor`, `gentle_ai.version`, `gentle_ai.install_choice`, `gentle_ai.sync_stale_accepted`, `answers.ides` (final confirmed agent list). Mark `wf_phase_done phase0b phase0c`.
> **Validation**: before `wf_phase_done`, verify critical fields are not null:
> ```bash
> jq -e '.gentle_ai.doctor != null and .gentle_ai.version != null and .answers.ides | type == "array"' .wizard-state.json || { echo "FAIL: state validation failed"; exit 1; }
> ```
> Tell the user: *"Phase 0 completed. Reply **continue** to choose which features to configure."*
> Wait for the response. Only when confirmed, run in bash:

---

═══════════════════════════════════════════════════════
⛔ PHASE 0b COMPLETE — Ready for Phase 0c
⏸ PAUSE — Waiting for user to confirm "continue"

### [WIZARD ACTION]
When user confirms, run EXACTLY:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Validate state before phase transition (phase-aware validation)
wf_phase_done phase0b phase0c
cat "$WF_DIR/phase0c.md"
```
