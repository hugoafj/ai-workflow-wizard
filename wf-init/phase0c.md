## PHASE 0c — Workflow feature selection

> This phase runs AFTER verifying gentle-ai and BEFORE discovery (Phase 1).
> The chosen features determine which wizard phases are executed and which
> protocols are packaged in AGENTS.md.

Read the current state (in case of resumption):

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

if [ -f .wizard-state.json ] && [ "$(jq -r '.phases.phase0c.status // "pending"' .wizard-state.json)" = "done" ]; then
  echo "Phase 0c already completed — skipping to Phase 1."
  wf_phase_done phase0c phase1
  cat "$WF_DIR/phase1.md"
  exit 0
fi
```

### Question — Feature selection

Try the IDE's structured input tool (`question`, `ask_user_question`,
`AskQuestion`, or equivalent) with all 6 options plus "none". If the
tool is unavailable or doesn't support that many options, display:

```
What features do you want to configure in this project? Choose the numbers
separated by commas, or "none":

────────────────────────────────────────────────────────────
1. 🪜 wf-ladder (anti-over-engineering — 7 rungs
   before implementing, without depending on wf-sdd-trigger or gentle-ai's SDD)

2. 🧪 wf-tdd (RED→GREEN per task. Independent from SDD
   — only requires configured tests)

3. 🚦 wf-sdd-trigger + wf-preflight + PRECHECK
   (this wizard's own policy for when to explicitly request gentle-ai's SDD:
   decision tree, wf-no-sdd/wf-force-sdd outcomes lock menu,
   PRECHECK enforcement gate. Never redecides how gentle-ai itself routes or
   delegates — that stays gentle-ai's own native authority)

4. 🔧 CI (Quality Guard + AI review + conventional commits
   + release-please + optional security review + hooks)

5. 🚀 CD (automatic deploy to VPS via GitHub Actions
   — PM2, Nginx+PHP-FPM, Docker)

6. 📦 Release-please only
   (automatic versioning on PRs via conventional commits +
   Husky hook. Only if you did NOT choose CI)
────────────────────────────────────────────────────────────

Examples:
  "1,2,3"  → Ladder + TDD + Routing (no CI/CD)
  "1,3,4"  → Ladder + Routing + CI (no CD)
  "4,5"    → Full CI + CD
  "6"      → Release-please only (automatic versioning)
  "none"   → Only .gitignore + maintenance commands (wf-onboard, wf-worktree, wf-settings)
```

**Wait for user response** (via structured input tool or plain text fallback).
Parse the selected features and proceed.

### Combination validations

- If they choose 4 and 6: "Release-please standalone is included in CI. Should I remove 6 and keep only 4? [yes / no]"
- If they choose 3 without 1: "SDD Routing activates the full SDD-forcing policy (wf-sdd-trigger + wf-preflight) but not the Ladder. If you want anti-over-engineering rungs, also add option 1. Should I add 1? [yes / no]"
- If they choose 5 without 4: "CD without CI works, but you won't have Quality Guard or AI review on your PRs. Do you confirm only CD? [yes / no]"

### Persistence

Save in `.wizard-state.json` under the `features` section:

```json
{
  "decision_ladder": <true/false based on option 1>,
  "tdd_protocol": <true/false based on option 2>,
  "routing_abc": <true/false based on option 3>,
  "ci": <true/false based on option 4>,
  "cd": <true/false based on option 5>,
  "release_please": <true/false based on option 6 or if they chose 4>
}
```

Mark `wf_phase_done phase0c phase1`.

Tell the user: *"Features selected. Reply **continue** to start project discovery."*

Wait for the response. Only when confirmed, run in bash:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"
wf_phase_done phase0c phase1
cat "$WF_DIR/phase1.md"
```
