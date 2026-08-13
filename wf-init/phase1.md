## PHASE 1 — Discovery report

> This phase delegates detection to a specialized sub-agent to save tokens
> in the main agent. The sub-agent runs bash commands, analyzes the output,
> saves the results in `.wizard-state.json` and returns a formatted report.

### Delegation to discovery sub-agent

1. Read the sub-agent prompt from `subagent-discovery.md`:
   ```bash
   cat "$WF_DIR/subagent-discovery.md"
   ```

2. Replace the placeholders in the prompt:
   - `{PROJECT_PATH}` → absolute path of the target project
   - `{WF_PATH}` → absolute path of the workflow wizard repo (`$WF_DIR/..`)
   - `{WF_RAW}` → `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`

3. Use the `task` tool with `subagent_type: general` to launch the sub-agent
   with the resolved prompt. Wait for it to finish and return the report.

4. When the sub-agent finishes, show the report to the user:

   ```
   DISCOVERY REPORT
   ================
   Detected stack: <stack>
   Code files: ~<N>
   Git commits: <N>

   Previous workflow artifacts:
     AGENTS.md: <exists / does not exist>
     CLAUDE.md: <exists / does not exist>
     Satellites: <list or "none">
     Post-commit hook: <exists / does not exist>

   Classification: GREENFIELD / LEGACY

   Should I continue with artifact migration? [yes]
   ```

   **PAUSE — Wait for user confirmation before continuing.**

### Persistence

The sub-agent already saved the data in `.wizard-state.json`. Just verify it exists:

```bash
cat .wizard-state.json | jq '.discovery, .migration, .phases'
```

If something is missing, complete it manually.

Tell the user: *"Discovery completed. Reply **continue** to review any previous artifacts to migrate."*

Wait for the response. Only when confirmed, run in bash:

```bash
source "$WF_DIR/lib/state-helpers.sh"
wf_phase_done phase1 phase2
cat "$WF_DIR/phase2.md"
```

> **CRITICAL**: `wf_phase_done` MUST execute before `cat phase2.md`. Do not skip this step — it marks phase1 as done and advances the pointer. Without it, phase1 stays pending.
