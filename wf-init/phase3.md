## PHASE 3 — Greenfield vs legacy classification

Determine the mode using these signals:

- **Greenfield** if: `git log` has fewer than 5 commits, or almost all code files are from the same day, or the `package.json` was created recently without significant production dependencies.
- **Legacy** if: there are commits with real history, there are significant production dependencies, there is code in `src/` with established patterns.

Inform and wait for confirmation:

```
Classification: GREENFIELD / LEGACY

Reason: <brief explanation based on signals>
```

Then ask explicitly with these visible options:

**Is this classification correct?**
- `yes` — correct, continue
- `no, it's greenfield` — correct and continue as greenfield
- `no, it's legacy` — correct and continue as legacy

**PAUSE — Wait for user response before continuing.**

**Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `discovery.classification` (`greenfield` | `legacy`). The routing below is decided by reading that field from state, not from memory.

- If the user confirms **LEGACY**: `wf_phase_done phase3 phase4`, then run in bash `cat "$WF_DIR/phase4.md"`
- If the project is **GREENFIELD**: mark `phases.phase4.status=skipped`, then compute the next phase based on the ALREADY SELECTED features:

```bash
NEXT=
if [ "$(jq -r '.features.routing_abc // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.tdd_protocol // false' .wizard-state.json)" = "true" ]; then
  NEXT="phase45"
elif [ "$(jq -r '.features.ci // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.cd // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.release_please // false' .wizard-state.json)" = "true" ]; then
  NEXT="phase47-cicd"
else
  NEXT="phase5"
fi
wf_phase_done phase3 "$NEXT"
cat "$WF_DIR/$NEXT.md"
```

> **⛔ STOP HERE — do not execute any cat until receiving the user's response.**
