## PHASE 0c — Workflow feature selection

> This phase runs AFTER verifying gentle-ai and BEFORE discovery (Phase 1).
> The chosen features determine which wizard phases are executed and which
> protocols are packaged in AGENTS.md.

Read the current state (in case of resumption):

```bash
if [ -f .wizard-state.json ] && [ "$(jq -r '.phases.phase0c // "pending"' .wizard-state.json)" = "done" ]; then
  echo "Phase 0c already completed — skipping to Phase 1."
  wf_phase_done phase0c phase1
  cat "$WF_DIR/phase1.md"
  exit 0
fi
```

### Question — Feature selection

```
What features do you want to configure in this project? Choose the numbers
separated by commas, or "none":

────────────────────────────────────────────────────────────
1. 🪜 Decision Ladder (anti-over-engineering — 7 rungs
   before implementing, without depending on routes or SDD)

2. 🧪 TDD Protocol (RED→GREEN per task. Independent from SDD
   — only requires configured tests)

3. 🚦 ABC Routes Protocol + Preflight + Precheck
   (Full Local Orchestration: decision tree, A/B/C routes,
   Route B lock menu, Precheck enforcement gate.
   Includes SDD Lite as a shortcut in Route B)

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
  "none"   → Only .gitignore + wf-refresh + maintenance commands
```

**Wait for user response.**

### Combination validations

- If they choose 4 and 6: "Release-please standalone is included in CI. Should I remove 6 and keep only 4? [yes / no]"
- If they choose 3 without 1: "ABC Routing includes full Local Orchestration but not the Ladder. If you want anti-over-engineering rungs, also add option 1. Should I add 1? [yes / no]"
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
cat "$WF_DIR/phase1.md"
```
