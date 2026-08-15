## PHASE 6 — Deterministic assembly (part B: Builder-Heavy)

> This phase assembles operations B7-B9: per-IDE commands, post-commit hook, testing configs,
> and CI/CD into `.wizard-staging/`. The staging already has AGENTS.md, protocols, and
> satellites from Builder-Core. **Preferred**: delegate to sub-agent. **Fallback**: run
> Builder inline if delegation unavailable.

### Step 1: Verify staging is ready

Builder-Core should have completed. Verify:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

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
   WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
   source "$WF_DIR/lib/state-helpers.sh"

   cat "$WF_DIR/subagent-builder-heavy.md"
   ```

2. Replace placeholders:
   - `{PROJECT_PATH}` → absolute path of the target project
   - `{WF_PATH}` → absolute path of the downloaded phase directory (`$WF_DIR`)
   - `{WF_RAW}` → `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`
   - `{WF_STAGING}` → `{PROJECT_PATH}/.wizard-staging`
   - `{WF_STATE}` → `{PROJECT_PATH}/.wizard-state.json`

3. Use `task` tool with `subagent_type: general` to launch Builder-Heavy. Wait for it.

4. Once finished, jump to **Step 4: Validation** below.

### Step 3: Fallback — inline Builder execution

If delegation is unavailable:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

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
# (.wizard-state.json stays at the project root, never in staging)
for artifact in AGENTS.md; do
  if [ ! -f ".wizard-staging/$artifact" ]; then
    echo "ERROR: Missing critical artifact: .wizard-staging/$artifact"
    exit 1
  fi
done

# Check that command files were actually generated for the active IDEs
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
FOUND=0
for IDE in $IDES; do
  case "$IDE" in
    claude-code)
      [ -n "$(find .wizard-staging/.claude/commands -maxdepth 1 -name 'wf-*.md' -print -quit 2>/dev/null)" ] && FOUND=$((FOUND + 1))
      ;;
    opencode)
      [ -n "$(find .wizard-staging/.opencode/commands -maxdepth 1 -name 'wf-*.md' -print -quit 2>/dev/null)" ] && FOUND=$((FOUND + 1))
      ;;
    cursor)
      [ -n "$(find .wizard-staging/.cursor/commands -maxdepth 1 -name 'wf-*.md' -print -quit 2>/dev/null)" ] && FOUND=$((FOUND + 1))
      ;;
    windsurf)
      [ -n "$(find .wizard-staging/.windsurf/workflows -maxdepth 1 -name 'wf-*.md' -print -quit 2>/dev/null)" ] && FOUND=$((FOUND + 1))
      ;;
    kiro)
      [ -n "$(find .wizard-staging/.kiro/steering -maxdepth 1 -name 'wf-*.md' -print -quit 2>/dev/null)" ] && FOUND=$((FOUND + 1))
      ;;
    vscode-copilot)
      [ -n "$(find .wizard-staging/.github/prompts -maxdepth 1 -name 'wf-*.prompt.md' -print -quit 2>/dev/null)" ] && FOUND=$((FOUND + 1))
      ;;
    codex)
      [ -n "$(find .wizard-staging/.codex/commands -maxdepth 1 -name 'wf-*.md' -print -quit 2>/dev/null)" ] && FOUND=$((FOUND + 1))
      ;;
    gemini-cli)
      [ -f ".wizard-staging/GEMINI.md" ] && FOUND=$((FOUND + 1))
      ;;
    antigravity)
      [ -n "$(find .wizard-staging/.agents/skills -maxdepth 2 -name 'SKILL.md' -print -quit 2>/dev/null)" ] && FOUND=$((FOUND + 1))
      ;;
  esac
done
if [ "$FOUND" -eq 0 ]; then
  echo "ERROR: No generated command files found in .wizard-staging for the active IDEs."
  echo "Builder-Heavy may have skipped or failed. Check .wizard-state.json answers.ides[] and command generation logs."
  exit 1
fi

echo "✓ Builder-Heavy validation passed"
```

### Step 5: Mark phases complete and inform user

Mark the Builder phases done and advance the pointer **only if the current phase_pointer is still one of the Builder phases**. This makes the phase safe to reuse during `/wf-refresh`, when the project may already be past phase 7:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

CURRENT_PHASE=$(jq -r '.phase_pointer // empty' .wizard-state.json)
# phase5 advances to phase6a-agents (the real key); phase6 is a backward-compatible alias.
if [ "$CURRENT_PHASE" = "phase6" ] || [ "$CURRENT_PHASE" = "phase6a-agents" ] || [ "$CURRENT_PHASE" = "phase6b-build-heavy" ]; then
  jq '.phases["phase6"].status = "done" |
      .phases["phase6a-agents"].status = "done" |
      .phases["phase6b-build-heavy"].status = "done" |
      .phase_pointer = "phase7" |
      .updated_at = (now | todate)' .wizard-state.json > .wizard-state.json.tmp
  mv .wizard-state.json.tmp .wizard-state.json
fi
```

Then inform the user:

```
All artifacts are assembled in .wizard-staging/.
Reply **continue** to see the full review before writing anything.
```

Wait for user confirmation. Only then:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

# During /wf-refresh the phase7 promotion is handled by the refresh flow, not here.
if [ "${WF_REFRESH:-0}" != "1" ]; then
  cat "$WF_DIR/phase7.md"
fi
```
