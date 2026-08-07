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

## Phase -1 · Check for deleted files (from manifest)

Before detection, check if there's a manifest with deleted files that the user should know about:

```bash
# Check if there's a WIZARD_MANIFEST in the project
if [ -f "WIZARD_MANIFEST.json" ] || [ -f ".wizard-manifests/WIZARD_MANIFEST-*.json" ]; then
  MANIFEST=$(find .wizard-manifests -name "WIZARD_MANIFEST-*.json" 2>/dev/null | head -1 || find . -name "WIZARD_MANIFEST.json" | head -1)
  
  if jq -e '._deleted_files' "$MANIFEST" 2>/dev/null > /dev/null; then
    echo "⚠️  WARNING: Some wizard files were deleted in recent releases:"
    echo ""
    jq -r '._deleted_files.files[]' "$MANIFEST" | while read deleted_file; do
      echo "  - $deleted_file"
    done
    echo ""
    echo "These files are no longer part of the wizard."
    echo "Cleaning up will remove them from your project."
    echo ""
    read -p "Continue? [yes / no]: " continue_choice
    if [ "$continue_choice" != "yes" ]; then
      echo "Cleanup cancelled."
      exit 0
    fi
  fi
fi
```

---

## Phase 0 · Wizard artifact detection

Scan the project to detect what the wizard installed:

```bash
echo "=== AI Workflow Wizard Artifacts ==="
echo ""

# 1. Wizard skills (Do NOT confuse with gentle-ai skills)
echo "📦 Wizard skills:"
for dir in .claude/skills .agents/skills .kiro/skills .codex/skills; do
  if [ -d "$dir" ]; then
    for skill in "$dir"/*/; do
      skill_name=$(basename "$skill")
      # gentle-ai skills: sdd-apply, sdd-propose, sdd-tasks, sdd-spec, sdd-design, sdd-explore, sdd-verify, sdd-archive, sdd-init, sdd-onboard, gentle-orchestrator
      # wizard skills: workflow, commands, cicd, ides, testing, architecture, wf-refresh, wf-onboard, wf-settings, wf-worktree, wf-cleanup
      case "$skill_name" in
        sdd-apply|sdd-propose|sdd-tasks|sdd-spec|sdd-design|sdd-explore|sdd-verify|sdd-archive|sdd-init|sdd-onboard|gentle-orchestrator)
          echo "  ⏭ $dir/$skill_name (gentle-ai — DO NOT delete)"
          ;;
        *)
          echo "  🗑 $dir/$skill_name (wizard)"
          ;;
      esac
    done
  fi
done

# 2. Wizard commands
echo ""
echo "📋 Wizard commands:"
for dir in .claude/commands .cursor/commands .windsurf/workflows .kiro/steering .github/prompts .opencode/commands .codex/commands; do
  if [ -d "$dir" ]; then
    for cmd in "$dir"/*; do
      cmd_name=$(basename "$cmd")
      case "$cmd_name" in
        wf-init|wf-refresh|wf-onboard|wf-settings|wf-worktree|wf-cicd|wf-cleanup|wf-ladder)
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
        echo "  🗑 $skills_dir/$skill_name (wizard)"
      fi
    done
  fi
done

# 3. Wizard satellites
echo ""
echo "📡 Wizard satellites:"
for f in CLAUDE.md GEMINI.md ANTIGRAVITY.md .github/copilot-instructions.md; do
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
      gemini-review.yml|claude-review.yml|gga-review.yml|quality-guard.yml|security-review.*.yml|ai-summary-job.*.yml|release-please.yml)
        echo "  🗑 $wf (wizard)"
        ;;
      *)
        echo "  ⏭ $wf_name (not from wizard)"
        ;;
    esac
  done
fi

# 5. Other wizard artifacts
echo ""
echo "📁 Other artifacts:"
[ -f ".wizard-state.json" ] && echo "  🗑 .wizard-state.json"
[ -f ".wf-status" ] && echo "  🗑 .wf-status"
[ -f ".commitlintrc.json" ] && echo "  🗑 .commitlintrc.json"
[ -f "post-commit" ] && echo "  🗑 post-commit (git hook)"
[ -d "openspec" ] && echo "  ⏭ openspec/ (gentle-ai — DO NOT delete)"
```

**PAUSE**. Show the complete inventory to the user and ask:

```
Wizard artifacts detected. What would you like to delete?

[w] All wizard artifacts (skills, commands, satellites, CI/CD, hooks)
[s] Only wizard skills
[c] Only wizard commands
[t] Only wizard satellites
[i] Only wizard CI/CD workflows
[o] Only other artifacts (hooks, configs)
[p] Customize — choose file by file
[n] Delete nothing — I just want to see what's there

Your choice:
```

---

## Phase 1 · Selected deletion

According to the user's choice:

### Option [w] — All

Delete ALL wizard artifacts detected in Phase 0. Before each group, show the diff and ask for confirmation:

```
I will delete:

Skills (6 files):
  - .claude/skills/workflow/SKILL.md
  - .claude/skills/commands/SKILL.md
  - .claude/skills/cicd/SKILL.md
  - .claude/skills/ides/SKILL.md
  - .claude/skills/testing/SKILL.md
  - .claude/skills/architecture/SKILL.md

Delete these? [yes / no]
```

Repeat for each group (commands, satellites, CI/CD, others).

### Option [s/c/t/i/o] — Specific group

Delete only the selected group, with the same confirmation logic.

### Option [p] — Customize

Iterate over each detected file and ask individually:

```
.claude/skills/workflow/SKILL.md — Delete? [y/n]
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

**PAUSE**. Show the resulting AGENTS.md and ask for confirmation before writing:

```
I will delete these wizard sections:
  - Commands
  - MCPs
  - wf-version footer

I will KEEP your custom content:
  - [list user sections found]

OK to proceed? [yes / no]
```

---

## Phase 3 · Commit

If the user confirmed:

```bash
git add -A
git commit -m "chore: remove AI Workflow Wizard artifacts

Removed:
- [list of deleted files]
- Cleaned AGENTS.md (removed wizard sections)
- Kept: [list of preserved files]"
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
- [N] wizard CI/CD workflows
- [N] other artifacts

Preserved:
- AGENTS.md (clean, without wizard sections)
- openspec/ (gentle-ai)
- [user files that were kept]

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
- **If there are no wizard artifacts**: report "No wizard artifacts found in
  this project. Would you like to verify manually?"
- **If the project has no AGENTS.md**: there is nothing to clean in AGENTS.md.
  Only delete the detected artifacts.
- **If the user has gentle-ai installed**: inform them that wf-cleanup does NOT
  uninstall it — that's manual with `gentle-ai uninstall`.
