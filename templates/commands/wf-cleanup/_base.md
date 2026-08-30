# /wf-cleanup — Workflow cleanup wizard

> Global uninstaller of the AI Workflow Wizard. Removes the artifacts that the wizard
> installed in a project, without touching gentle-ai or user files.
>
> **When to use it**: when you want to uninstall the wizard from a project — you no longer
> need the rules, protocols, or CI/CD that the wizard configured.
>
> **What it does NOT touch**: gentle-ai files (base AGENTS.md, MCPs, Engram, OpenSpec),
> project code, user configuration.

---

## Inviolable rules

1. **DO NOT touch gentle-ai**: do not delete gentle-ai's `~/.claude/skills/`, do not modify
   MCPs configured by gentle-ai, do not touch Engram or OpenSpec.
2. **DO NOT touch project code**: do not delete files that were not created
   by the wizard.
3. **DO NOT push**: the user decides when to publish.
4. **Confirm before each deletion**: show what will be deleted and wait for `yes`.
5. **Preserve AGENTS.md**: the AGENTS.md file is cleaned of wizard content
   but kept if the user wants to preserve their own sections.

---

## Phase -1 · Check for wizard-managed files

Before detection, read the managed paths from `.wizard-state.json` (`build_plan.managed_paths`); fall back to `.wizard-managed-files.json` only if `.wizard-state.json` or its `build_plan.managed_paths` field is missing:

```bash
# Source of truth: .wizard-state.json build_plan.managed_paths
MANAGED_FILES=""
STATE_HAS_MANAGED_PATHS=false
if [ -f ".wizard-state.json" ] && jq -e '.build_plan.managed_paths' ".wizard-state.json" >/dev/null 2>&1; then
  STATE_HAS_MANAGED_PATHS=true
  MANAGED_FILES=$(jq -r '.build_plan.managed_paths[] // empty' ".wizard-state.json" 2>/dev/null || echo "")
  echo "ℹ Found wizard-managed paths in .wizard-state.json"
fi

# Fallback to .wizard-managed-files.json (legacy)
if [ "$STATE_HAS_MANAGED_PATHS" != "true" ] && [ -f ".wizard-managed-files.json" ]; then
  echo "ℹ Falling back to .wizard-managed-files.json"
  MANAGED_FILES=$(jq -r '.files[] | .path' ".wizard-managed-files.json" 2>/dev/null || echo "")
fi

if [ -n "$MANAGED_FILES" ]; then
  echo "ℹ Wizard-managed files to be removed:"
  echo "$MANAGED_FILES" | while read file; do
    echo "  - $file"
  done
  echo ""
fi
```

---

## Phase 0 · Wizard artifact detection

Scan the project to detect what the wizard installed:

```bash
echo "=== AI Workflow Wizard Artifacts ==="
echo ""

# 0. Manifest-authoritative candidates. build_plan.managed_paths is THE source of
# truth for what the wizard installed: classify every manifest path present on disk
# as wizard-owned BEFORE the heuristic scan below. Heuristics remain as a safety net
# for orphaned artifacts from installs that predate the manifest. Self-contained
# block (re-reads state — fenced blocks may run in fresh shells).
MANAGED_PATHS=""
if [ -f ".wizard-state.json" ]; then
  MANAGED_PATHS=$(jq -r '.build_plan.managed_paths[]? // empty' ".wizard-state.json" 2>/dev/null || true)
fi
if [ -n "$MANAGED_PATHS" ]; then
  echo "📜 Manifest-classified wizard-owned paths (authoritative):"
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    case "$p" in
      AGENTS.md)
        echo "  ⚙ $p (special → Phase 2 cleans its content, never deletes the file)"
        ;;
      .gitignore)
        echo "  ⚙ $p (special → revert wizard entries only, keep the file)"
        ;;
      .claude/settings.json|.claude/settings.local.json|.cursor/mcp.json|.windsurf/mcp.json)
        echo "  ⚙ $p (special → remove only the wizard MCP entry)"
        ;;
      .windsurf/workflows/sdd-new.md)
        echo "  ⏭ $p (gentle-ai bridge — DO NOT delete)"
        ;;
      *)
        [ -e "$p" ] && echo "  🗑 $p (manifest)"
        ;;
    esac
  done <<< "$MANAGED_PATHS"
  echo ""
fi

# 1. Wizard skills (Do NOT confuse with gentle-ai skills)
echo "📦 Wizard skills:"
for dir in .claude/skills .cursor/skills .gemini/skills .agents/skills .kiro/skills .codex/skills .opencode/skills .windsurf/skills .devin/skills .github/skills; do
  if [ -d "$dir" ]; then
    for skill in "$dir"/*/; do
      skill_name=$(basename "$skill")
      # gentle-ai skills: sdd-apply, sdd-propose, sdd-tasks, sdd-spec, sdd-design, sdd-explore, sdd-verify, sdd-archive, sdd-init, sdd-onboard, gentle-orchestrator
      # wizard skills (7 commands): wf-ladder, wf-tdd, wf-orchestrator, wf-sdd-trigger, wf-onboard, wf-worktree, wf-settings
      case "$skill_name" in
        sdd-apply|sdd-propose|sdd-tasks|sdd-spec|sdd-design|sdd-explore|sdd-verify|sdd-archive|sdd-init|sdd-onboard|gentle-orchestrator)
          echo "  ⏭ $dir/$skill_name (gentle-ai — DO NOT delete)"
          ;;
        wf-ladder|wf-tdd|wf-orchestrator|wf-sdd-trigger|wf-onboard|wf-worktree|wf-settings)
          echo "  🗑 $dir/$skill_name (wizard)"
          ;;
        *)
          echo "  ⏸ $dir/$skill_name (unknown — skipping)"
          ;;
      esac
    done
  fi
done

# 2. Wizard commands
# NOTE: .windsurf/workflows/sdd-new.md is INTENTIONALLY not classified as wizard-owned.
# gentle-ai creates that file; the wizard only overwrites it to apply a fix, and
# gentle-ai sync may rewrite it. Landing in "not from wizard" is correct — never
# delete it, and do not "fix" this classification to treat it as wizard-owned.
echo ""
echo "📋 Wizard commands:"
for dir in .claude/commands .cursor/commands .windsurf/workflows .kiro/steering .github/prompts .opencode/commands .codex/commands; do
  if [ -d "$dir" ]; then
    for cmd in "$dir"/*; do
      cmd_name=$(basename "$cmd")
      # Normalize filenames: command files use .md or .prompt.md extensions
      cmd_base=${cmd_name%.prompt.md}
      cmd_base=${cmd_base%.md}
      case "$cmd_base" in
        wf-init|wf-refresh|wf-onboard|wf-settings|wf-worktree|wf-cicd|wf-cleanup|wf-ladder|wf-tdd|tdd|wf-orchestrator|wf-sdd-trigger)
          echo "  🗑 $cmd (wizard)"
          ;;
        *)
          echo "  ⏭ $cmd_name (not from wizard)"
          ;;
      esac
    done
  fi
done

# Check .windsurf/skills and .devin/skills (structured with SKILL.md)
for skills_dir in .windsurf/skills .devin/skills; do
  if [ -d "$skills_dir" ]; then
    for skill in "$skills_dir"/*/SKILL.md; do
      if [ -f "$skill" ]; then
        skill_name=$(basename "$(dirname "$skill")")
        # Exclude gentle-ai skills from deletion
        case "$skill_name" in
          sdd-apply|sdd-propose|sdd-tasks|sdd-spec|sdd-design|sdd-explore|sdd-verify|sdd-archive|sdd-init|sdd-onboard|gentle-orchestrator)
            echo "  ⏭ $skills_dir/$skill_name (gentle-ai — DO NOT delete)"
            ;;
          wf-ladder|wf-tdd|wf-orchestrator|wf-sdd-trigger|wf-onboard|wf-worktree|wf-settings)
            echo "  🗑 $skills_dir/$skill_name (wizard)"
            ;;
          *)
            echo "  ⏸ $skills_dir/$skill_name (unknown — skipping)"
            ;;
        esac
      fi
    done
  fi
done

# 3. Wizard satellites
echo ""
echo "📡 Wizard satellites:"
for f in CLAUDE.md GEMINI.md ANTIGRAVITY.md .github/copilot-instructions.md \
         .cursor/rules/project.mdc .windsurf/rules/project.md .devin/rules/project.md \
         .kiro/steering/project-context.md; do
  if [ -f "$f" ]; then
    echo "  🗑 $f (wizard)"
  fi
done

# 3b. Wizard protocols (flat files — the universal fallback, protocol `ides`)
echo ""
echo "📄 Wizard protocols (flat):"
for f in .agents/protocols/*.md; do
  if [ -f "$f" ]; then
    echo "  🗑 $f (wizard)"
  fi
done

# 4. Wizard CI/CD workflows
echo ""
echo "⚙️ Wizard CI/CD workflows:"
if [ -d ".github/workflows" ]; then
  for wf in .github/workflows/*; do
    wf_name=$(basename "$wf")
    case "$wf_name" in
      gemini-review.yml|claude-review.yml|gga-review.yml|quality-guard.yml|security-review*.yml|ai-summary-job.*.yml|release-please.yml|deploy.yml)
        echo "  🗑 $wf (wizard)"
        ;;
      *)
        echo "  ⏭ $wf_name (not from wizard)"
        ;;
    esac
  done
fi

# 4b. MCP settings (Playwright MCP registered by the wizard in phase8)
echo ""
echo "🔌 Wizard MCP settings:"
for f in .claude/settings.json .claude/settings.local.json .cursor/mcp.json .windsurf/mcp.json; do
  if [ -f "$f" ] && grep -q "playwright" "$f" 2>/dev/null; then
    echo "  🗑 $f (wizard — Playwright MCP entry)"
  fi
done

# 4c. Test configs (injected by the wizard — may also hold user settings)
echo ""
echo "🧪 Wizard test configs:"
for f in vitest.config.ts playwright.config.ts; do
  if [ -f "$f" ]; then
    echo "  🗑 $f (wizard — review before deleting: may contain your own settings)"
  fi
done

# 5. Other wizard artifacts
echo ""
echo "📁 Other artifacts:"
[ -f ".wizard-state.json" ] && echo "  🗑 .wizard-state.json"
[ -f ".wizard-managed-files.json" ] && echo "  🗑 .wizard-managed-files.json"
[ -f "refresh-plan.json" ] && echo "  🗑 refresh-plan.json (from /wf-refresh)"
[ -f ".wizard-refresh-baseline.json" ] && echo "  🗑 .wizard-refresh-baseline.json (from /wf-refresh R3)"
[ -f ".wf-status" ] && echo "  🗑 .wf-status"
[ -f ".commitlintrc.json" ] && echo "  🗑 .commitlintrc.json"
[ -d ".husky" ] && echo "  🗑 .husky/ (conventional commits)"
[ -f ".gga" ] && echo "  🗑 .gga (GGA config)"
[ -f ".pr_agent.toml" ] && echo "  🗑 .pr_agent.toml"
[ -f "release-please-config.json" ] && echo "  🗑 release-please-config.json"
[ -f ".release-please-manifest.json" ] && echo "  🗑 .release-please-manifest.json"
[ -f ".git/hooks/post-commit" ] && echo "  🗑 .git/hooks/post-commit (git hook installed by the wizard)"
[ -d ".wizard-staging" ] && echo "  🗑 .wizard-staging/ (leftover from an interrupted run)"
[ -d "openspec" ] && echo "  ⏭ openspec/ (gentle-ai — DO NOT delete)"
if [ -f ".gitignore" ] && grep -qE "^\.wf-status$|^\.wizard-state\.json$|^\.wizard-managed-files\.json$|^\.wizard-staging/$|^!\.agents/$|^!\.cursor/$|^!\.windsurf/$|^!\.devin/$|^!\.kiro/$|^!\.claude/$|^!\.codex/$|^!\.opencode/$|^!\.gemini/$|^!GEMINI\.md$|^!ANTIGRAVITY\.md$|^!\.github/copilot-instructions\.md$|^!\.github/prompts/$" .gitignore; then
  echo "  🗑 .gitignore (wizard entries — review which ones to revert)"
fi
```

**Merge rule**: when `.wizard-state.json` has `build_plan.managed_paths`, it is the
authority — build the final inventory as the UNION of the manifest-classified list
(block 0) and the heuristic scan above, deduplicating overlapping entries. The
heuristic patterns stay as a safety net for orphans (installs older than the manifest).

**PAUSE**. Show the complete inventory and ask the user to write freely what to keep:

```
Wizard artifacts detected (see the inventory above).

Write, in your own words, what you want to KEEP. Examples:
  "keep .husky/ and release-please-config.json"
  "keep the cursor satellite and vitest.config.ts"
  "keep nothing — delete all wizard artifacts"
  "delete nothing — I just want to see what's here"

Everything wizard-owned that you did not mention will be deleted.
```

**Wait for the free-text response.**

Then build the deletion list:

1. **Parse the response**: anything the user mentioned is PRESERVED; everything
   else in the inventory is a deletion candidate. If the user wrote "keep nothing",
   every wizard artifact is a candidate. If they wrote "delete nothing", stop here.
2. **Show the resulting deletion list grouped by type and confirm** (inviolable
   rule: confirm before each deletion):

```
I will delete:

Skills (N files):
  - ...

Commands (N files):
  - ...

Satellites (N files):
  - ...

Protocols flat (N files):
  - ...

CI/CD workflows (N files):
  - ...

MCP settings (N files):
  - ...

Test configs (N files):
  - ...

Other artifacts (N files):
  - ...

Preserved (your choice): <list>

Delete these? [yes / no]
```

- `yes`: continue to Phase 1.
- `no`: show the inventory again and repeat the "what do you want to keep?" question.

---

## Phase 1 · Delete the confirmed groups

Delete each group confirmed in Phase 0, group by group, and report each one.
Never delete gentle-ai artifacts (`sdd-*`, `gentle-orchestrator`, `openspec/`,
`~/.<ide>/`).

### Skills

Remove each wizard skill directory detected in Phase 0 (only wizard ones — never
`sdd-*` or `gentle-orchestrator`):

```bash
# Example per detected wizard skill (replace with the actual list — all 7 wizard
# commands ship skills 1:1, in native IDE paths AND the universal .agents/skills/)
rm -rf .claude/skills/wf-ladder .claude/skills/wf-tdd \
       .claude/skills/wf-orchestrator .claude/skills/wf-sdd-trigger \
       .claude/skills/wf-onboard .claude/skills/wf-worktree .claude/skills/wf-settings \
       .cursor/skills/wf-ladder .cursor/skills/wf-tdd \
       .cursor/skills/wf-orchestrator .cursor/skills/wf-sdd-trigger \
       .cursor/skills/wf-onboard .cursor/skills/wf-worktree .cursor/skills/wf-settings \
       .gemini/skills/wf-ladder .gemini/skills/wf-tdd \
       .gemini/skills/wf-orchestrator .gemini/skills/wf-sdd-trigger \
       .gemini/skills/wf-onboard .gemini/skills/wf-worktree .gemini/skills/wf-settings \
       .kiro/skills/wf-ladder .kiro/skills/wf-tdd \
       .kiro/skills/wf-orchestrator .kiro/skills/wf-sdd-trigger \
       .kiro/skills/wf-onboard .kiro/skills/wf-worktree .kiro/skills/wf-settings \
       .codex/skills/wf-ladder .codex/skills/wf-tdd \
       .codex/skills/wf-orchestrator .codex/skills/wf-sdd-trigger \
       .codex/skills/wf-onboard .codex/skills/wf-worktree .codex/skills/wf-settings \
       .opencode/skills/wf-ladder .opencode/skills/wf-tdd \
       .opencode/skills/wf-orchestrator .opencode/skills/wf-sdd-trigger \
       .opencode/skills/wf-onboard .opencode/skills/wf-worktree .opencode/skills/wf-settings \
       .windsurf/skills/wf-ladder .windsurf/skills/wf-tdd \
       .windsurf/skills/wf-orchestrator .windsurf/skills/wf-sdd-trigger \
       .windsurf/skills/wf-onboard .windsurf/skills/wf-worktree .windsurf/skills/wf-settings \
       .devin/skills/wf-ladder .devin/skills/wf-tdd \
       .devin/skills/wf-orchestrator .devin/skills/wf-sdd-trigger \
       .devin/skills/wf-onboard .devin/skills/wf-worktree .devin/skills/wf-settings \
       .agents/skills/wf-ladder .agents/skills/wf-tdd \
       .agents/skills/wf-orchestrator .agents/skills/wf-sdd-trigger \
       .agents/skills/wf-onboard .agents/skills/wf-worktree .agents/skills/wf-settings \
       .github/skills/wf-ladder .github/skills/wf-tdd \
       .github/skills/wf-orchestrator .github/skills/wf-sdd-trigger \
       .github/skills/wf-onboard .github/skills/wf-worktree .github/skills/wf-settings
```

### Commands

Remove each wizard command file detected in Phase 0:

```bash
# Example per detected wizard command
rm -f .claude/commands/wf-settings.md
```

### Satellites

Remove each wizard satellite detected in Phase 0:

```bash
rm -f CLAUDE.md GEMINI.md ANTIGRAVITY.md .github/copilot-instructions.md \
      .cursor/rules/project.mdc .windsurf/rules/project.md .devin/rules/project.md \
      .kiro/steering/project-context.md
```

### Protocols flat

Remove each wizard protocol in `.agents/protocols/` detected in Phase 0:

```bash
rm -f .agents/protocols/wf-orchestrator.md
```

### CI/CD workflows

Remove each wizard workflow detected in Phase 0:

```bash
rm -f .github/workflows/quality-guard.yml .github/workflows/deploy.yml
```

### MCP settings

For each MCP settings file detected, remove only the wizard's Playwright MCP
entry. If the file only contained that entry, delete the file.

### Test configs

For each test config detected, remove the wizard-injected blocks. If the user
confirmed deleting the whole file, delete it.

### Other artifacts

Remove the remaining detected items:

```bash
rm -f .wizard-state.json .wf-status .commitlintrc.json .gga .pr_agent.toml
rm -f .wizard-managed-files.json
rm -f refresh-plan.json .wizard-refresh-baseline.json
rm -f release-please-config.json .release-please-manifest.json
rm -rf .husky .wizard-staging
rm -f .git/hooks/post-commit
```

Revert the wizard entries in `.gitignore` (the lines detected in Phase 0).

### Node projects · package.json reconciliation

If `.husky/` deletion was confirmed and `package.json` exists, detect what init
left behind: `/wf-init` Phase 8 runs `npx husky init` (adds `"prepare": "husky"`
to package.json) and installs commitlint as a devDependency. Without this step,
the NEXT `npm install` runs `prepare` → husky recreates `.husky/_` and
reconfigures `core.hooksPath`: the wizard partially resurrects itself after an
uninstall.

```bash
# Detection (read-only):
if [ -f package.json ]; then
  jq -r '.scripts.prepare // empty' package.json | grep -qx 'husky' \
    && echo '⚠ scripts.prepare = "husky" remains — npm install will recreate .husky/_'
  jq -r '.devDependencies // {} | keys[]' package.json | grep -E '^(husky|commitlint|@commitlint/)' || true
fi
git config --get core.hooksPath 2>/dev/null   # may still point to .husky
```

Offer to reconcile and WAIT for an explicit `yes` (never run automatically):

```bash
# Only after yes:
npm pkg delete scripts.prepare
npm uninstall husky commitlint @commitlint/cli @commitlint/config-conventional 2>/dev/null || true
# Only when core.hooksPath pointed into .husky:
git config --unset core.hooksPath 2>/dev/null || true
```

### Report broken npm scripts

If any test config was deleted (`vitest.config.ts`, `playwright.config.ts`, …)
and `package.json` exists, report which npm scripts now reference deleted
configs — otherwise CI breaks mysteriously weeks later with no clue why:

```bash
if [ -f package.json ]; then
  # List ONLY the test configs actually deleted in this run:
  DELETED_CONFIGS="vitest.config.ts playwright.config.ts"
  jq -r '.scripts // {} | to_entries[] | "\(.key)\t\(.value)"' package.json | while IFS=$'\t' read -r name value; do
    for cfg in $DELETED_CONFIGS; do
      case "$value" in *"$cfg"*) echo "⚠ Script '$name' references deleted $cfg";; esac
    done
  done
fi
```

After each group, report:

```
✓ Deleted: <group> (<N> files)
```

---

## Phase 2 · AGENTS.md cleanup

After deleting the artifacts, clean up AGENTS.md **but preserve all custom user content**:

### What to DELETE (wizard-generated only):

1. **"Commands" section** (the `/wf-refresh`, `/wf-init` table)
2. **"Project MCPs" section** (the gentle-ai entries generated by wizard)
3. **`wf-version` footer** (the HTML comment at the end with version number)
4. **"Behavior Preferences"** specific to wizard (review gate, no opportunistic refactor, drift detection)

### What to KEEP (all custom user content):

- ✅ **Sections marked with `<!-- WF: DO NOT REGENERATE -->`** — these are sacred
- ✅ **Custom rules/policies** you added manually (team standards, release windows, etc.)
- ✅ **Custom sections** not from the wizard (anything outside Commands, Code Style, Structure, Constraints, Checks, MCPs, Behavior)
- ✅ **Project code and documentation** references you added

**Golden Rule**: When in doubt, KEEP IT. Only delete what the wizard clearly injected.

```bash
# Detect wizard-generated vs custom content:
# Wizard generates: Commands, Code Style, Project Structure, Critical Constraints,
# Programmatic Checks, MCPs, Behavior Preferences
# Everything else = custom user content = PRESERVE
```

**PAUSE**. Show the resulting AGENTS.md and ask the user to write freely what to keep:

```
Here is the AGENTS.md with the wizard sections removed.

Write, in your own words, what you want to KEEP (for example:
  "keep the Commands section", "keep the MCPs table",
  "keep everything about SDD"). Examples of wizard sections:
  - Commands
  - MCPs
  - wf-version footer
  - Behavior Preferences (wizard-specific)

Everything else stays deleted. OK to proceed? [free text]
```

**Wait for the free-text response.** Reinsert whatever the user asked to keep,
then confirm the final result once more before writing:

---

## Phase 3 · Commit

If the user confirmed:

```bash
git add -A
git commit -m "chore: remove AI Workflow Wizard artifacts

Removed:
- [list of deleted files]
- Cleaned AGENTS.md (removed wizard sections)
- Kept: [list of preserved files / sections]"
```

NO `git push`.

---

## Final output

```
Cleanup complete.

Deleted:
- [N] wizard skills
- [N] wizard commands
- [N] wizard satellites
- [N] wizard protocols
- [N] wizard CI/CD workflows
- [N] MCP settings / test configs
- [N] other artifacts

Preserved (your choice):
- AGENTS.md (clean, without wizard sections)
- openspec/ (gentle-ai)
- [user files / sections that were kept]

Commit: <hash>

Next steps:
1. If you want to reinstall the wizard, run /wf-init.
2. If you want to also remove gentle-ai, uninstall it manually with
   `gentle-ai uninstall` or by removing gentle-ai's ~/.claude/skills/.
```

---

## Technical rules

- **gentle-ai vs wizard detection**: gentle-ai skills have specific
  names (sdd-apply, sdd-propose, etc.). Wizard skills are: workflow,
  commands, cicd, ides, testing, architecture, wf-refresh, wf-onboard,
  wf-settings, wf-worktree, wf-cleanup.
- **Confirmation flow**: after the inventory, the user writes freely what to
  keep (in their own words, files or groups). Everything wizard-owned they did
  not mention is deleted, after a per-group confirmation.
- **MCP settings and test configs may mix wizard and user content**: when the
  user does not mention them, remove only the wizard-injected parts
  (Playwright MCP entry, coverage/snapshot blocks), not the whole file.
- **If there are no wizard artifacts**: report "No wizard artifacts found in
  this project. Would you like to verify manually?"
- **If the project has no AGENTS.md**: there is nothing to clean in AGENTS.md.
  Only delete the detected artifacts.
- **If AGENTS.md ends up EMPTY after Phase 2 cleanup**: delete the file
  (`rm AGENTS.md`) and report it explicitly in the final output. An empty
  AGENTS.md serves nobody.
- **If the user has gentle-ai installed**: inform them that wf-cleanup does NOT
  uninstall it — that's manual with `gentle-ai uninstall`.
