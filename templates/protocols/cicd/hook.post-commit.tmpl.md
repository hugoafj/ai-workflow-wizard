```bash
#!/bin/bash
# Workflow drift detector — AI Workflow Wizard
# Detects three categories of drift on each commit and only notifies.

# Files that trigger /wf-refresh (general project context for AI)
REFRESH_FILES="package.json composer.json pyproject.toml Cargo.toml \
  tsconfig.json vite.config.ts vite.config.js \
  next.config.ts next.config.js \
  tailwind.config.ts tailwind.config.js"

# Files that trigger an sdd-init refresh (project capabilities tracked by SDD)
SDD_FILES="package.json \
  vitest.config.ts vitest.config.js \
  jest.config.ts jest.config.js \
  playwright.config.ts playwright.config.js"
# openspec/config.yaml is excluded: it is the output of the sdd-init skill.
# Including it causes a loop: sdd-init writes the file → commit → hook notifies
# re-run sdd-init → guaranteed loop.

# Config/IDE files that trigger /wf-refresh (AGENTS.md, IDE settings, satellites, commands)
CONFIG_FILES="AGENTS.md \
  .claude/settings.json .cursor/settings.json .windsurf/settings.json .kiro/settings.json .opencode/config.json \
  .claude/commands .cursor/commands .windsurf/workflows .kiro/steering .opencode/commands .codex/commands \
  .github/copilot-instructions.md .github/prompts \
  .claude/skills .cursor/skills .windsurf/skills .devin/skills .kiro/skills .codex/skills .opencode/skills .gemini/skills \
  .agents/protocols .agents/skills"

CHANGED_REFRESH=""
CHANGED_SDD=""

# Use git diff-tree to list files in the just-created commit.
# This works for the first commit and after subsequent commits, unlike
# `git diff --cached` which sees an empty index immediately post-commit.
CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null)

# Check if this is a wizard refresh commit
COMMIT_MSG=$(git log -1 --pretty=%B HEAD 2>/dev/null || true)
IS_WIZARD_REFRESH=false
if echo "$COMMIT_MSG" | grep -q "^chore: refresh workflow to v"; then
  IS_WIZARD_REFRESH=true
fi

# A wizard refresh commit writes wizard-managed files BY DESIGN: AGENTS.md,
# IDE commands/satellites/skills, vitest/playwright configs, hooks. Warning
# about them seconds after applying would self-trigger the very flow that
# produced the commit (field report B2), so refresh commits never raise drift.
# openspec/config.yaml is excluded for the same loop reason (see note above).
if [[ "$IS_WIZARD_REFRESH" = "true" ]]; then
  exit 0
fi

for f in $REFRESH_FILES; do
  if echo "$CHANGED" | grep -qxF "$f"; then
    CHANGED_REFRESH="$CHANGED_REFRESH $f"
  fi
done

for f in $SDD_FILES; do
  if echo "$CHANGED" | grep -qxF "$f"; then
    CHANGED_SDD="$CHANGED_SDD $f"
  fi
done

# Detect changes in config files (AGENTS.md, IDE settings, satellites, commands)
CHANGED_CONFIG=""
for pattern in $CONFIG_FILES; do
  # Escape the pattern so dots in paths like .claude/settings.json are treated literally
  esc_pattern=$(printf '%s' "$pattern" | sed 's/[][^.$*?+{}|()\\-]/\\&/g')
  # Match exact files or any path under a directory prefix
  if echo "$CHANGED" | grep -qE "^${esc_pattern}(/|$)"; then
    if [ -d "$pattern" ]; then
      CHANGED_CONFIG="$CHANGED_CONFIG $pattern/"
    else
      CHANGED_CONFIG="$CHANGED_CONFIG $pattern"
    fi
  fi
done

# Exit cleanly if no drift
if [ -z "$CHANGED_REFRESH" ] && [ -z "$CHANGED_SDD" ] && [ -z "$CHANGED_CONFIG" ]; then
  exit 0
fi

# 1. Print a stderr warning
printf '\n┌─────────────────────────────────────────────────────┐\n' >&2
printf '│  ⚠  Workflow context may need refresh              │\n' >&2
printf '└─────────────────────────────────────────────────────┘\n' >&2

if [ -n "$CHANGED_REFRESH" ]; then
  printf '  AGENTS.md drift:%s\n' "$CHANGED_REFRESH" >&2
  printf '  → Run /wf-refresh in your IDE/CLI\n' >&2
fi

if [ -n "$CHANGED_SDD" ]; then
  printf '  SDD drift:%s\n' "$CHANGED_SDD" >&2
  printf '  → Run the sdd-init skill (slash: /sdd-init, or /gentle-sdd-init in Claude Code)\n' >&2
fi

if [ -n "$CHANGED_CONFIG" ]; then
  printf '  Config/IDE files changed:%s\n' "$CHANGED_CONFIG" >&2
  printf '  → Run /wf-refresh to sync AGENTS.md and protocols\n' >&2
fi

printf '\n' >&2

# 2. Create persistent .wf-status
COMMIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
COMMIT_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date)

{
  echo "# ⚠ Workflow drift detected"
  echo ""
  echo "**Commit**: $COMMIT_HASH"
  echo "**Date**: $COMMIT_DATE"
  echo ""

  if [ -n "$CHANGED_REFRESH" ]; then
    echo "## AGENTS.md drift"
    echo ""
    echo "The following files changed and may leave AGENTS.md out of date:"
    echo ""
    for f in $CHANGED_REFRESH; do echo "- \`$f\`"; done
    echo ""
    echo "**Action**: run \`/wf-refresh\` in your IDE/CLI to update AGENTS.md,"
    echo "or \`rm .wf-status\` if these changes don't affect AI context."
    echo ""
  fi

  if [ -n "$CHANGED_SDD" ]; then
    echo "## SDD drift"
    echo ""
    echo "The following files changed and may affect SDD project capabilities"
    echo "(test frameworks, build config, dependencies, SDD config):"
    echo ""
    for f in $CHANGED_SDD; do echo "- \`$f\`"; done
    echo ""
    echo "**Action**: run the \`sdd-init\` skill to refresh SDD context"
    echo "(slash: \`/sdd-init\`, or \`/gentle-sdd-init\` in Claude Code),"
    echo "or \`rm .wf-status\` if these changes don't affect SDD."
    echo ""
  fi

  if [ -n "$CHANGED_CONFIG" ]; then
    echo "## Config/IDE files changed"
    echo ""
    echo "The following config or IDE files changed and may affect AI context:"
    echo ""
    for pattern in $CHANGED_CONFIG; do echo "- \`$pattern\`"; done
    echo ""
    echo "**Action**: run \`/wf-refresh\` to sync AGENTS.md and protocols,"
    echo "or \`rm .wf-status\` if these changes don't affect AI context."
    echo ""
  fi

  echo "---"
  echo "_This file persists across IDE sessions until you act on it._"
  echo "_Delete it with \`rm .wf-status\` once resolved._"
} > .wf-status

# 3. Native macOS notification
if command -v osascript > /dev/null 2>&1; then
  NOTIF_TEXT=""
  [ -n "$CHANGED_REFRESH" ] && NOTIF_TEXT="Run /wf-refresh"
  [ -n "$CHANGED_SDD" ] && NOTIF_TEXT="${NOTIF_TEXT:+$NOTIF_TEXT · }sdd-init (Claude Code: /gentle-sdd-init)"
  [ -n "$CHANGED_CONFIG" ] && NOTIF_TEXT="${NOTIF_TEXT:+$NOTIF_TEXT · }Config/IDE drift"
  osascript -e "display notification \"$NOTIF_TEXT\" with title \"⚠ Workflow drift detected\"" 2>/dev/null || true
fi

# 4. Opportunistically refresh gentle-ai's skill registry so its own Skill Resolver
#    Protocol picks up this wizard's wf-* skills without the user having to remember
#    to run it manually. Confirmed against gentle-ai's own source that it never scans
#    .windsurf/skills/ or .devin/skills/; those discover project skills natively.
if command -v gentle-ai >/dev/null 2>&1; then
  gentle-ai skill-registry refresh --quiet >/dev/null 2>&1 || true
fi

exit 0
```
