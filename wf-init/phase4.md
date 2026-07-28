## PHASE 4 — Reverse engineering (legacy only)

Read the code to detect real conventions:

```bash
# Examples of main components/modules
ls src/ 2>/dev/null
find src -name "*.tsx" -o -name "*.ts" | head -20 2>/dev/null
# Read 2-3 representative files to detect patterns
```

Report the detected conventions and **wait for correction or confirmation**:

```
DETECTED CONVENTIONS
====================
Naming: <camelCase / PascalCase / kebab-case / snake_case>
Component structure: <observed pattern>
Imports: <absolute / relative / alias>
Tests: <detected framework / no tests>
CSS: <Tailwind / CSS modules / styled-components / plain CSS>
State: <useState / Zustand / Redux / Context / other>

Is this correct? Fix any errors before continuing.
  [yes] — all correct, continue
  [fix: <describe the error>] — adjust the incorrect field and show again
```

**PAUSE — Wait for user response. If they correct something, update and show again before continuing.**

---
> **⛔ STOP HERE — do not execute anything else.**
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `discovery.conventions` (the detected/corrected conventions from reverse engineering). Mark `wf_phase_done phase4 <next>`.
> Compute the next phase based on the ALREADY SELECTED features:
> ```bash
> if [ "$(jq -r '.features.routing_abc // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.tdd_protocol // false' .wizard-state.json)" = "true" ]; then
>   echo "phase45"
> elif [ "$(jq -r '.features.ci // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.cd // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.release_please // false' .wizard-state.json)" = "true" ]; then
>   echo "phase47-cicd"
> else
>   echo "phase6a-agents"
> fi
> ```
> Wait for the response. Only when the user confirms with "yes", run in bash: `cat "$WF_DIR/$NEXT.md"`
