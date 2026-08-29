## PHASE 4 — Reverse engineering (legacy only)

Read the code to detect real conventions:

```bash
# Examples of main components/modules
ls src/ 2>/dev/null
find src -name "*.tsx" -o -name "*.ts" | head -20 2>/dev/null
# Read 2-3 representative files to detect patterns

# Detect test directory convention
find . -path ./node_modules -prune -o -type f \( -name '*.test.*' -o -name '*.spec.*' \) -print 2>/dev/null | head -5 | xargs -I{} dirname {} | sort -u
```

Report the detected conventions and **wait for correction or confirmation**:

```
DETECTED CONVENTIONS
====================
Naming: <camelCase / PascalCase / kebab-case / snake_case>
Component structure: <observed pattern>
Imports: <absolute / relative / alias>
Tests: <detected framework / no tests>
Test directory: <detected test dir, e.g. src/__tests__ or src/test>
CSS: <Tailwind / CSS modules / styled-components / plain CSS>
State: <useState / Zustand / Redux / Context / other>

Is this correct? Fix any errors before continuing.
  [yes] — all correct, continue
  [fix: <describe the error>] — adjust the incorrect field and show again
```

**PAUSE — Wait for user response. If they correct something, update and show again before continuing.**

---
> **⛔ STOP HERE — do not execute anything else.**
> **Persistence**: use `wf_state_set` or the `edit` tool to save in `.wizard-state.json` → `discovery.conventions` (the detected/corrected conventions from reverse engineering) AND `discovery.test_dir` (the detected test directory, e.g. `src/__tests__` or `src/test`). Mark `wf_phase_done phase4 <next>`.
> Compute the next phase based on ALREADY SELECTED features. If any have been activated, route to the relevant conditional phase; otherwise phase5:
> Wait for the response. Only when the user confirms with "yes", run in bash:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# Validate state before phase transition (phase-aware validation)
NEXT=
if [ "$(jq -r '.features.routing_abc // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.tdd_protocol // false' .wizard-state.json)" = "true" ]; then
  NEXT="phase45"
elif [ "$(jq -r '.features.ci // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.cd // false' .wizard-state.json)" = "true" ] || [ "$(jq -r '.features.release_please // false' .wizard-state.json)" = "true" ]; then
  NEXT="phase47-cicd"
else
  NEXT="phase5"
fi
wf_phase_done phase4 "$NEXT"
echo "ℹ Next phase: $NEXT"
cat "$WF_DIR/$NEXT.md"
```
