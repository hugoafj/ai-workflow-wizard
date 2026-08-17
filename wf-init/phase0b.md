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
SYNC_OUTPUT=$(gentle-ai sync --dry-run 2>&1)
```

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

- If `sync now`: run `gentle-ai sync`, show its output, then re-run `gentle-ai sync --dry-run` to
  confirm it now reports no pending changes before continuing to Step 0.5.
- If `continue anyway`: record this decision in `.wizard-state.json` (`gentle_ai.sync_stale_accepted
  = true`) so `wf-refresh` can surface it again later, and continue to Step 0.5.

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
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `gentle_ai.doctor` (doctor result), `answers.ides` (final confirmed agent list). Mark `wf_phase_done phase0b phase0c`.
> Tell the user: *"Phase 0 completed. Reply **continue** to choose which features to configure."*
> Wait for the response. Only when confirmed, run in bash:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"
wf_phase_done phase0b phase0c
cat "$WF_DIR/phase0c.md"
```
