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
> Wait for the response. Only when confirmed, run in bash: `cat "$WF_DIR/phase0c.md"`
