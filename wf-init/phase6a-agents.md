## PHASE 6 — Deterministic assembly (part A: Builder-Core)

> This phase assembles operations B1-B6: AGENTS.md, packaged protocols, and per-IDE
> satellites into `.wizard-staging/`. **Preferred**: delegate to sub-agent to save tokens.
> **Fallback**: run Builder inline if delegation is unavailable (older IDEs, certain contexts).

### Step 1: Check if delegation is available

Try the delegation path first (most efficient):

```bash
# Attempt to get Builder-Core prompt for delegation
BUILDER_CORE_PROMPT=$(cat "$WF_DIR/subagent-builder-core.md" 2>/dev/null)
if [ -z "$BUILDER_CORE_PROMPT" ]; then
  echo "ERROR: Cannot read subagent-builder-core.md"
  exit 1
fi
```

### Step 2: Attempt delegation (preferred path)

If your agent environment supports the `task` tool:

1. Replace placeholders in the prompt:
   - `{PROJECT_PATH}` → absolute path of the target project
   - `{WF_PATH}` → absolute path of the downloaded phase directory (`$WF_DIR`)
   - `{WF_RAW}` → `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`

2. Use `task` tool with `subagent_type: general` to launch Builder-Core. Wait for it.

3. Once finished, jump to **Step 4: Validation** below.

### Step 3: Fallback — inline Builder execution

If delegation is unavailable (older Windsurf, Devin, CI/CD contexts, or any agent without `task` tool):

```bash
cat "$WF_DIR/lib/builder.md"
```

Read and execute the Builder procedure inline. It is deterministic and mechanical — no decisions required, just follow the steps for B1-B6 (Load state, Resolve keys, Assemble protocols, Build artifacts, Write to staging).

### Step 4: Validation — verify staging was populated

Regardless of delegation or inline execution, validate that `.wizard-staging/` was created and contains expected files:

```bash
if [ ! -d .wizard-staging ]; then
  echo "ERROR: .wizard-staging/ was not created."
  echo "This means Builder-Core (B1-B6) did not complete successfully."
  echo ""
  echo "Troubleshooting:"
  echo "  1. Check .wizard-state.json is valid: cat .wizard-state.json | jq ."
  echo "  2. If delegated: check sub-agent output above for errors"
  echo "  3. If inline: check that you followed all steps in lib/builder.md"
  echo ""
  echo "Re-run with: cat \"$WF_DIR/phase6a-agents.md\""
  exit 1
fi

echo "=== Staging directory created ==="
find .wizard-staging -type f | wc -l
echo "files in .wizard-staging/"

# Verify key artifacts exist (.wizard-state.json stays at the project root,
# never in staging — staging holds only generated files)
for artifact in AGENTS.md; do
  if [ ! -f ".wizard-staging/$artifact" ]; then
    echo "ERROR: Missing critical artifact: .wizard-staging/$artifact"
    echo "Builder-Core did not complete correctly. Check steps above."
    exit 1
  fi
done

echo "✓ Builder-Core validation passed"
```

### Step 5: Continue to Builder-Heavy

If validation succeeds, continue with part B:

```bash
cat "$WF_DIR/phase6b-build-heavy.md"
```
