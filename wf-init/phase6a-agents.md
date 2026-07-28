## PHASE 6 — Deterministic assembly (part A: Builder-Core)

> This phase delegates operations B1-B6 to a specialized sub-agent to save
> tokens in the main agent. The sub-agent assembles AGENTS.md, packaged
> protocols, and per-IDE satellites into `.wizard-staging/`.

### Delegation to Builder-Core sub-agent

1. Read the sub-agent prompt from `subagent-builder-core.md`:
   ```bash
   cat "$WF_DIR/subagent-builder-core.md"
   ```

2. Replace the placeholders in the prompt:
   - `{PROJECT_PATH}` → absolute path of the target project
   - `{WF_PATH}` → absolute path of the workflow wizard repo (`$WF_DIR/..`)
   - `{WF_RAW}` → `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`

3. Use the `task` tool with `subagent_type: general` to launch the
   Builder-Core sub-agent with the resolved prompt. Wait for it to finish.

4. When the sub-agent finishes, verify the staging has the expected files:
   ```bash
   ls -la .wizard-staging/
   find .wizard-staging -type f | sort
   ```

5. If everything is in order, continue automatically with part B (Builder-Heavy):
   ```bash
   cat "$WF_DIR/phase6b-build-heavy.md"
   ```

### In case of error

If the sub-agent reports an error or the staging is empty, stop and show:
```
ERROR: Builder-Core failed. Check the sub-agent output above.
Possible causes:
  - .wizard-state.json has missing required fields
  - No connection to GitHub raw (curl failed)
  - The sub-agent ran out of tokens

Fix the issue and re-run this phase with:
  cat .wizard-state.json   (verify state)
  cat "$WF_DIR/phase6a-agents.md"   (re-execute)
```
