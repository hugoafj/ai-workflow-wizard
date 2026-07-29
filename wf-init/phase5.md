## PHASE 5 — Minimum project questions

> The features WERE ALREADY SELECTED in Phase 0c. Here we only ask
> project details that don't depend on the features.

**Question 1 — Project name** (if not obvious from package.json):
```
What is this project called? (for AGENTS.md)
```

**Question 2 — Exact stack** (if there is ambiguity):
```
Detected: <stack>. Correct versions? For example: React 19.2, Vite 8.0, TypeScript 6.0, Tailwind 4.0
```

**Question 3 — Critical constraints** (only if the project has something non-standard):
```
Is there any critical constraint the agent must NEVER violate in this project?
Examples: "don't install dependencies without approval", "never touch src/legacy/",
"the main branch is protected".
[none / <brief description>]
```

**PAUSE after each question or as a block — wait for responses before continuing.**

### Persistence

Save in `.wizard-state.json` → `answers.project_name`, `answers.stack_versions`, `answers.critical_constraints`.

Mark `wf_phase_done phase5 phase6a-agents`.

Tell the user: *"Questions completed. Reply **continue** so I can assemble the artifacts (Builder → staging on disk, not in memory)."*

Wait for the response. Only when confirmed, run in bash:

```bash
cat "$WF_DIR/phase6a-agents.md"
```
