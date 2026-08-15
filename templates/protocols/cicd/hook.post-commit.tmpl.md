```bash
#!/bin/bash
# Workflow drift detector — AI Workflow Wizard
# Detect changes that warrant /wf-refresh and/or /sdd-init.

# Files that warrant /wf-refresh (general project context for AI)
REFRESH_FILES="package.json composer.json pyproject.toml Cargo.toml tsconfig.json vite.config.ts vite.config.js next.config.ts next.config.js tailwind.config.ts tailwind.config.js"

# Files that warrant /sdd-init refresh (project capabilities that SDD tracks)
# package.json also applies here because it affects test/build scripts detected by sdd-init
SDD_FILES="package.json vitest.config.ts vitest.config.js jest.config.ts jest.config.js playwright.config.ts playwright.config.js"
# openspec/config.yaml excluded: it is the output artifact of /sdd-init, not a trigger.
# Including it causes a loop: /sdd-init writes the file → commit → hook notifies
# re-runs /sdd-init → guaranteed loop.

CHANGED_REFRESH=""
CHANGED_SDD=""

for f in $REFRESH_FILES; do
  if git diff HEAD~1 HEAD --name-only 2>/dev/null | grep -q "^$f$"; then
    CHANGED_REFRESH="$CHANGED_REFRESH $f"
  fi
done

for f in $SDD_FILES; do
  if git diff HEAD~1 HEAD --name-only 2>/dev/null | grep -q "^$f$"; then
    CHANGED_SDD="$CHANGED_SDD $f"
  fi
done

if [ -n "$CHANGED_REFRESH" ] || [ -n "$CHANGED_SDD" ]; then
  # 1. Print to stderr (better compatibility with IDEs that hide stdout)
  printf '\n┌─────────────────────────────────────────────────────┐\n' >&2
  printf '│  ⚠  Workflow context may need refresh              │\n' >&2
  printf '└─────────────────────────────────────────────────────┘\n' >&2
  [ -n "$CHANGED_REFRESH" ] && printf '  AGENTS.md drift:%s\n' "$CHANGED_REFRESH" >&2
  [ -n "$CHANGED_REFRESH" ] && printf '  Run: /wf-refresh\n' >&2
  [ -n "$CHANGED_SDD" ] && printf '  SDD drift:%s\n' "$CHANGED_SDD" >&2
  [ -n "$CHANGED_SDD" ] && printf '  Run: /sdd-init to refresh SDD project capabilities\n' >&2
  printf '\n' >&2

  # 2. Create persistent .wf-status file
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
      echo "Files changed that affect AI agent context:"
      for f in $CHANGED_REFRESH; do echo "- $f"; done
      echo ""
      echo "**Action**: run \`/wf-refresh\` to update AGENTS.md, or \`rm .wf-status\` if the changes don't affect AI context."
      echo ""
    fi
    if [ -n "$CHANGED_SDD" ]; then
      echo "## SDD drift"
      echo ""
      echo "Files changed that affect SDD project capabilities (test frameworks, build config, dependencies):"
      for f in $CHANGED_SDD; do echo "- $f"; done
      echo ""
      echo "**Action**: run \`/sdd-init\` in your IDE/CLI to refresh SDD context, or \`rm .wf-status\` if the changes don't affect SDD."
      echo ""
    fi
    echo "This file persists across IDE sessions until you act on it."
  } > .wf-status

  # 3. macOS notification
  if command -v osascript &>/dev/null; then
    NOTIF_TEXT=""
    [ -n "$CHANGED_REFRESH" ] && NOTIF_TEXT="Run /wf-refresh"
    [ -n "$CHANGED_SDD" ] && NOTIF_TEXT="${NOTIF_TEXT:+$NOTIF_TEXT and }/sdd-init"
    osascript -e "display notification \"$NOTIF_TEXT\" with title \"⚠ Workflow drift detected\"" 2>/dev/null || true
  fi
fi

# 4. Opportunistically refresh gentle-ai's skill registry so its own Skill Resolver
#    Protocol picks up this wizard's wf-* skills (wf-orchestrator, wf-ladder,
#    wf-sdd-trigger, wf-tdd) without the user having to remember to run
#    it manually. Helps Claude Code/OpenCode/Cursor/Kiro/Codex (orchestrators that read
#    .atl/skill-registry.md before delegating). Harmless no-op for Windsurf/Devin — confirmed
#    against gentle-ai's own source that it never scans .windsurf/skills/ or .devin/skills/;
#    those discover project skills natively from the filesystem instead. Cheap no-op
#    (cache-hit) when nothing under skills/ changed. Silent and non-blocking: never fail the
#    commit.
if command -v gentle-ai &>/dev/null; then
  gentle-ai skill-registry refresh --quiet >/dev/null 2>&1 || true
fi

exit 0
```
