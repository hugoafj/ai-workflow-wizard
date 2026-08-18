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

### Step 2: Run Builder-Heavy (deterministic script)

Builder-Heavy is a deterministic Python script — no sub-agent delegation, no inline fallback:

```bash
WF_DIR="${WF_DIR:-/tmp/wf-init-phases}"
source "$WF_DIR/lib/state-helpers.sh"

python3 "$WF_DIR/lib/builder-heavy.py" \
  --state ".wizard-state.json" \
  --staging ".wizard-staging" \
  --raw "${WF_RAW:-https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main}" \
  --wf-dir "$WF_DIR"
```

- `--state` → `.wizard-state.json` (project root; the script writes back `build_plan` and advances the phase pointer).
- `--staging` → `.wizard-staging`.
- `--raw` → the wizard raw base (same as `WF_RAW` used by `/wf-init`).
- `--wf-dir` → the downloaded phase directory (`$WF_DIR`).
- The script implements B7-B9: per-IDE commands, post-commit hook, testing configs, CI/CD, registration + advance. It exits non-zero on any unresolved placeholder or missing template.

If Builder-Core did not run yet (no `AGENTS.md` in staging), run it first:

```bash
python3 "$WF_DIR/lib/builder-core.py" \
  --state ".wizard-state.json" \
  --staging ".wizard-staging" \
  --raw "${WF_RAW:-https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main}" \
  --wf-dir "$WF_DIR"
```

### Step 3: (removed — deterministic script replaces the inline fallback)

Builder-Heavy is executed exclusively via the Python script in Step 2. There is no
sub-agent or manual inline path anymore; `lib/builder.md` is kept only as a
specification reference.

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

# Check that the always-included command files were generated for each active IDE
# (Builder-Heavy writes wf-worktree/wf-settings/wf-onboard unconditionally).
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)
FAILED=0
for IDE in $IDES; do
  case "$IDE" in
    claude-code)
      for cmd in wf-worktree wf-settings wf-onboard; do
        [ -f ".wizard-staging/.claude/commands/$cmd.md" ] || { echo "ERROR: missing .claude/commands/$cmd.md"; FAILED=1; }
      done
      ;;
    opencode)
      for cmd in wf-worktree wf-settings wf-onboard; do
        [ -f ".wizard-staging/.opencode/commands/$cmd.md" ] || { echo "ERROR: missing .opencode/commands/$cmd.md"; FAILED=1; }
      done
      ;;
    cursor)
      for cmd in wf-worktree wf-settings wf-onboard; do
        [ -f ".wizard-staging/.cursor/commands/$cmd.md" ] || { echo "ERROR: missing .cursor/commands/$cmd.md"; FAILED=1; }
      done
      ;;
    windsurf)
      for cmd in wf-worktree wf-settings wf-onboard; do
        [ -f ".wizard-staging/.windsurf/workflows/$cmd.md" ] || { echo "ERROR: missing .windsurf/workflows/$cmd.md"; FAILED=1; }
      done
      ;;
    kiro)
      for cmd in wf-worktree wf-settings wf-onboard; do
        [ -f ".wizard-staging/.kiro/steering/$cmd.md" ] || { echo "ERROR: missing .kiro/steering/$cmd.md"; FAILED=1; }
      done
      ;;
    vscode-copilot)
      for cmd in wf-worktree wf-settings wf-onboard; do
        [ -f ".wizard-staging/.github/prompts/$cmd.prompt.md" ] || { echo "ERROR: missing .github/prompts/$cmd.prompt.md"; FAILED=1; }
      done
      ;;
    codex)
      for cmd in wf-worktree wf-settings wf-onboard; do
        [ -f ".wizard-staging/.codex/commands/$cmd.md" ] || { echo "ERROR: missing .codex/commands/$cmd.md"; FAILED=1; }
      done
      ;;
    gemini-cli)
      [ -f ".wizard-staging/GEMINI.md" ] || { echo "ERROR: missing GEMINI.md"; FAILED=1; }
      ;;
    antigravity)
      for cmd in wf-worktree wf-settings wf-onboard; do
        [ -d ".wizard-staging/.agents/skills/$cmd" ] || { echo "ERROR: missing .agents/skills/$cmd"; FAILED=1; }
      done
      ;;
  esac
done
if [ "$FAILED" -ne 0 ]; then
  IDE_COUNT=$(jq -r '(.answers.ides // []) | length' .wizard-state.json)
  if [ "$IDE_COUNT" -eq 0 ]; then
    echo "WARNING: No active IDE/CLI selected — skipping command file validation."
  else
    echo "ERROR: Missing generated command files in .wizard-staging for the active IDEs."
    echo "Builder-Heavy may have skipped or failed. Check .wizard-state.json answers.ides[] and command generation logs."
    exit 1
  fi
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
# During /wf-refresh the phase7 promotion is handled by the refresh flow, not here.
if [ "${WF_REFRESH:-0}" != "1" ] && { [ "$CURRENT_PHASE" = "phase6" ] || [ "$CURRENT_PHASE" = "phase6a-agents" ] || [ "$CURRENT_PHASE" = "phase6b-build-heavy" ]; }; then
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
