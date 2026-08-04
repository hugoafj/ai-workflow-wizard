## PHASE 6 — Deterministic assembly (part B: Builder-Heavy)

> This phase assembles operations B7-B9: per-IDE commands, post-commit hook, testing configs,
> and CI/CD into `.wizard-staging/`. The staging already has AGENTS.md, protocols, and
> satellites from Builder-Core. **Preferred**: delegate to sub-agent. **Fallback**: run
> Builder inline if delegation unavailable.

### Step 1: Verify staging is ready

Builder-Core should have completed. Verify:

```bash
if [ ! -d .wizard-staging ] || [ ! -f .wizard-staging/AGENTS.md ]; then
  echo "ERROR: Builder-Core staging not found or incomplete."
  echo "Phase 6a must complete successfully before running 6b."
  echo ""
  echo "Re-run: cat \"$WF_DIR/phase6a-agents.md\""
  exit 1
fi
echo "✓ Builder-Core staging verified"
```

### Step 2: Attempt delegation (preferred path)

If your agent environment supports the `task` tool:

1. Read the sub-agent prompt:
   ```bash
   cat "$WF_DIR/subagent-builder-heavy.md"
   ```

2. Replace placeholders:
   - `{PROJECT_PATH}` → absolute path of the target project
   - `{WF_PATH}` → absolute path of the workflow wizard repo (`$WF_DIR/..`)
   - `{WF_RAW}` → `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`

3. Use `task` tool with `subagent_type: general` to launch Builder-Heavy. Wait for it.

4. Once finished, jump to **Step 4: Validation** below.

### Step 3: Fallback — inline Builder execution

If delegation is unavailable:

```bash
cat "$WF_DIR/lib/builder.md"
```

Read and execute the Builder procedure inline for operations B7-B9 (add per-IDE commands, post-commit hook, testing configs, CI/CD). It is deterministic — follow the steps for writing to `.wizard-staging/`.

### Step 4: Validation — verify complete staging

Regardless of delegation or inline, validate the complete assembly:

```bash
if [ ! -d .wizard-staging ]; then
  echo "ERROR: .wizard-staging/ was lost or not updated."
  echo "Builder-Heavy (B7-B9) did not complete successfully."
  exit 1
fi

echo "=== Staging files ==="
find .wizard-staging -type f | sort
echo ""
echo "=== build_plan ==="
jq '.build_plan' .wizard-state.json 2>/dev/null || echo "(no build_plan in state yet)"

# Verify critical files from both Builder-Core and Builder-Heavy
for artifact in AGENTS.md .wizard-state.json; do
  if [ ! -f ".wizard-staging/$artifact" ]; then
    echo "ERROR: Missing critical artifact: .wizard-staging/$artifact"
    exit 1
  fi
done

# Check that at least one IDE command was added (proof Builder-Heavy ran)
IDE_COMMANDS=$(find .wizard-staging -name "*.md" -type f | xargs grep -l "IDE command" 2>/dev/null | wc -l)
if [ "$IDE_COMMANDS" -eq 0 ]; then
  echo "WARNING: No IDE commands found in staging. Builder-Heavy may have skipped or failed."
  echo "Check that .wizard-state.json has valid answers.ides[] configuration."
fi

echo "✓ Builder-Heavy validation passed"
```

### Step 5: Mark phases complete and inform user

Mark phases 6 and 7 as done (persistence):

```bash
wf_phase_done phase6 phase7
```

Then inform the user:

```
All artifacts are assembled in .wizard-staging/.
Reply **continue** to see the full review before writing anything.
```

Wait for user confirmation. Only then:

```bash
cat "$WF_DIR/phase7.md"
```
