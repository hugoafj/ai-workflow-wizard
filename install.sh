#!/bin/bash
# AI Workflow Wizard — Global command installer
# Installs /wf-init, /wf-refresh, and /wf-cleanup as global slash commands (1:1 with skills).
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/install.sh | bash -s -- --uninstall
#
# Source: github.com/hugoafj/ai-workflow-wizard

set -eo pipefail

REPO="hugoafj/ai-workflow-wizard"
BRANCH="main"
RAW="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

COMMANDS="wf-init wf-refresh wf-cleanup"

# ── Helpers ──────────────────────────────────────────────────────────

fetch_cmd() {
  local cmd="$1"

  curl -fsSL "${RAW}/templates/commands/${cmd}/_base.md" 2>/dev/null && return 0

  echo "FAILED: could not fetch templates/commands/${cmd}/_base.md"
  exit 1
}

install_plain() {
  local dir="$1" cmd="$2" content="$3" version="$4"
  mkdir -p "$dir"
  printf -- '<!-- wf-cmd-version: %s -->\n%s\n' "$version" "$content" > "${dir}/${cmd}.md"
  echo "  ✓ ${dir}/${cmd}.md"
}

install_windsurf() {
  local dir="$1" cmd="$2" content="$3" desc="$4" version="$5"
  mkdir -p "$dir"
  printf -- '---\ndescription: %s\nversion: %s\n---\n\n%s\n' "$desc" "$version" "$content" \
    > "${dir}/${cmd}.md"
  echo "  ✓ ${dir}/${cmd}.md"
}

install_kiro() {
  local dir="$1" cmd="$2" content="$3" version="$4"
  mkdir -p "$dir"
  printf -- '---\ninclusion: manual\nversion: %s\n---\n\n%s\n' "$version" "$content" \
    > "${dir}/${cmd}.md"
  echo "  ✓ ${dir}/${cmd}.md"
}

install_antigravity() {
  local dir="$1" cmd="$2" content="$3" desc="$4" version="$5"
  local skill_dir="${dir}/skills/${cmd}"
  mkdir -p "$skill_dir"
  printf -- '---\nname: %s\ndescription: %s\nversion: %s\n---\n\n%s\n' \
    "$cmd" "$desc" "$version" "$content" > "${skill_dir}/SKILL.md"
  echo "  ✓ ${skill_dir}/SKILL.md"
}

install_copilot() {
  local dir="$1" cmd="$2" content="$3" desc="$4" version="$5"
  local skill_dir="${dir}/skills/${cmd}"
  mkdir -p "$skill_dir"
  printf -- '---\nname: %s\ndescription: %s\nversion: %s\n---\n\n%s\n' \
    "$cmd" "$desc" "$version" "$content" > "${skill_dir}/SKILL.md"
  echo "  ✓ ${skill_dir}/SKILL.md"
}

install_agents_skills() {
  local dir="$1" cmd="$2" content="$3" desc="$4" version="$5"
  local skill_dir="${dir}/${cmd}"
  mkdir -p "$skill_dir"
  printf -- '---\nname: %s\ndescription: %s\nversion: %s\n---\n\n%s\n' \
    "$cmd" "$desc" "$version" "$content" > "${skill_dir}/SKILL.md"
  echo "  ✓ ${skill_dir}/SKILL.md"
}

# ── Install ──────────────────────────────────────────────────────────

do_install() {
  # Detect IDEs
  local has_claude=0 has_cursor=0 has_windsurf=0 has_kiro=0
  local has_codex=0 has_copilot=0 has_antigravity=0 has_opencode=0 has_devin=0
  local ide_count=0

  [[ -d "$HOME/.claude" ]]          && has_claude=1      && ide_count=$((ide_count + 1))
  [[ -d "$HOME/.cursor" ]]          && has_cursor=1      && ide_count=$((ide_count + 1))
  [[ -d "$HOME/.codeium/windsurf" ]] && has_windsurf=1    && ide_count=$((ide_count + 1))
  [[ -d "$HOME/.kiro" ]]            && has_kiro=1        && ide_count=$((ide_count + 1))
  [[ -d "$HOME/.codex" ]]           && has_codex=1       && ide_count=$((ide_count + 1))
  [[ -d "$HOME/.copilot" ]]         && has_copilot=1     && ide_count=$((ide_count + 1))
  [[ -d "$HOME/.gemini" ]]          && has_antigravity=1 && ide_count=$((ide_count + 1))
  [[ -d "$HOME/.config/opencode" ]] && has_opencode=1    && ide_count=$((ide_count + 1))
  [[ -d "$HOME/.config/devin" ]]    && has_devin=1       && ide_count=$((ide_count + 1))

  if [[ $ide_count -eq 0 ]]; then
    echo "No supported IDEs detected. Install one of: Claude Code, Cursor,"
    echo "Windsurf, Kiro, Codex, Copilot, Antigravity, OpenCode, or Devin, then re-run."
    exit 1
  fi

  echo "Detected ${ide_count} IDE(s). Installing global commands + skills..."
  echo ""

  # Fetch remote version
  echo -n "Fetching remote version... "
  local VERSION
  VERSION=$(curl -fsSL "${RAW}/VERSION" 2>/dev/null | head -1)
  VERSION=${VERSION#v}
  echo "${VERSION}"
  echo ""

  # Descriptions for Windsurf/Antigravity frontmatter
  local desc_init="AI Workflow Wizard bootstrap — initialize the workflow in a new repo"
  local desc_refresh="AI Workflow Wizard refresh — re-run the builder-driven generator and apply hash-based diffs when the project evolves"
  local desc_cleanup="AI Workflow Wizard uninstaller — remove wizard artifacts from a project"

  local installed=0

  for cmd in $COMMANDS; do
    echo -n "Fetching /${cmd}... "
    local body
    body=$(fetch_cmd "$cmd")
    echo "OK"

    local desc=""
    [[ "$cmd" == "wf-init" ]]    && desc="$desc_init"
    [[ "$cmd" == "wf-refresh" ]] && desc="$desc_refresh"
    [[ "$cmd" == "wf-cleanup" ]] && desc="$desc_cleanup"

    if [[ $has_claude -eq 1 ]]; then
      install_plain "$HOME/.claude/commands" "$cmd" "$body" "$VERSION"
      installed=$((installed + 1))
      install_agents_skills "$HOME/.claude/skills" "$cmd" "$body" "$desc" "$VERSION"
      installed=$((installed + 1))
    fi
    if [[ $has_cursor -eq 1 ]]; then
      install_plain "$HOME/.cursor/commands" "$cmd" "$body" "$VERSION"
      installed=$((installed + 1))
      install_agents_skills "$HOME/.cursor/skills" "$cmd" "$body" "$desc" "$VERSION"
      installed=$((installed + 1))
    fi
    if [[ $has_windsurf -eq 1 ]]; then
      # Windsurf legacy global workflows (flat .md, frontmatter description required)
      install_windsurf "$HOME/.codeium/windsurf/global_workflows" "$cmd" "$body" "$desc" "$VERSION"
      installed=$((installed + 1))
      # Windsurf legacy global skills (safety net for older Windsurf channels)
      install_agents_skills "$HOME/.codeium/windsurf/skills" "$cmd" "$body" "$desc" "$VERSION"
      installed=$((installed + 1))
      # Devin path (Windsurf rebrand) — only when Devin itself is not detected
      if [[ $has_devin -eq 0 ]]; then
        install_copilot "$HOME/.config/devin" "$cmd" "$body" "$desc" "$VERSION"
        installed=$((installed + 1))
      fi
    fi
    if [[ $has_devin -eq 1 ]]; then
      install_copilot "$HOME/.config/devin" "$cmd" "$body" "$desc" "$VERSION"
      installed=$((installed + 1))
    fi
    if [[ $has_kiro -eq 1 ]]; then
      install_kiro "$HOME/.kiro/steering" "$cmd" "$body" "$VERSION"
      installed=$((installed + 1))
    fi
    # Unconditional: .agents/skills is read by Codex, OpenCode, Gemini (AGY app),
    # and Devin — the universal skill fallback for every IDE/CLI (1:1 command ↔ skill).
    # NOTE: AGY CLI does NOT read ~/.agents/skills/ — Antigravity CLI/IDE
    # coverage comes from the ~/.gemini/antigravity-cli/builtin + ~/.gemini/config
    # installs below (config/skills is the only global path all three read).
    install_agents_skills "$HOME/.agents/skills" "$cmd" "$body" "$desc" "$VERSION"
    installed=$((installed + 1))
    if [[ $has_codex -eq 1 ]]; then
      install_plain "$HOME/.codex/commands" "$cmd" "$body" "$VERSION"
      installed=$((installed + 1))
      install_agents_skills "$HOME/.codex/skills" "$cmd" "$body" "$desc" "$VERSION"
      installed=$((installed + 1))
    fi
    if [[ $has_copilot -eq 1 ]]; then
      install_copilot "$HOME/.copilot" "$cmd" "$body" "$desc" "$VERSION"
      installed=$((installed + 1))
    fi
    if [[ $has_antigravity -eq 1 ]]; then
      # CLI path
      install_antigravity "$HOME/.gemini/antigravity-cli/builtin" "$cmd" "$body" "$desc" "$VERSION"
      # IDE path (workaround for gentle-ai#746)
      install_antigravity "$HOME/.gemini/config" "$cmd" "$body" "$desc" "$VERSION"
      installed=$((installed + 2))
    fi
    if [[ $has_opencode -eq 1 ]]; then
      install_plain "$HOME/.config/opencode/commands" "$cmd" "$body" "$VERSION"
      installed=$((installed + 1))
      install_agents_skills "$HOME/.config/opencode/skills" "$cmd" "$body" "$desc" "$VERSION"
      installed=$((installed + 1))
    fi
  done

  echo ""
  echo "Installed ${installed} files. Restart your IDE."
  echo ""
  echo "Run /wf-init to start. If your IDE/CLI doesn't support slash commands,"
  echo "invoke it as a skill (e.g. type the skill name in natural language)."
}

# ── Uninstall ────────────────────────────────────────────────────────

do_uninstall() {
  echo "This will remove globally installed AI Workflow Wizard commands:"
  for cmd in $COMMANDS; do
    echo "  · /${cmd}"
  done
  echo ""
  echo "Project-specific commands will NOT be touched."
  echo ""
  read -p "Continue? [y/N] " confirm
  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Cancelled."
    exit 0
  fi

  local removed=0

  for cmd in $COMMANDS; do
    local f

    f="$HOME/.claude/commands/${cmd}.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    f="$HOME/.claude/skills/${cmd}/SKILL.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    f="$HOME/.cursor/commands/${cmd}.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    f="$HOME/.cursor/skills/${cmd}/SKILL.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    # Windsurf legacy global workflows + skills
    f="$HOME/.codeium/windsurf/global_workflows/${cmd}.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    f="$HOME/.codeium/windsurf/skills/${cmd}/SKILL.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    f="$HOME/.config/devin/skills/${cmd}/SKILL.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    f="$HOME/.kiro/steering/${cmd}.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    f="$HOME/.codex/commands/${cmd}.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    f="$HOME/.codex/skills/${cmd}/SKILL.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    f="$HOME/.agents/skills/${cmd}/SKILL.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    # Copilot
    f="$HOME/.copilot/skills/${cmd}/SKILL.md"
    if [[ -f "$f" ]]; then
      rm -rf "$HOME/.copilot/skills/${cmd}"
      echo "  ✓ Removed ~/.copilot/skills/${cmd}/"
      removed=$((removed + 1))
    fi

    # Antigravity CLI
    f="$HOME/.gemini/antigravity-cli/builtin/skills/${cmd}/SKILL.md"
    if [[ -f "$f" ]]; then
      rm -rf "$HOME/.gemini/antigravity-cli/builtin/skills/${cmd}"
      echo "  ✓ Removed ~/.gemini/antigravity-cli/builtin/skills/${cmd}/"
      removed=$((removed + 1))
    fi
    # Antigravity IDE
    f="$HOME/.gemini/config/skills/${cmd}/SKILL.md"
    if [[ -f "$f" ]]; then
      rm -rf "$HOME/.gemini/config/skills/${cmd}"
      echo "  ✓ Removed ~/.gemini/config/skills/${cmd}/"
      removed=$((removed + 1))
    fi

    f="$HOME/.config/opencode/commands/${cmd}.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))

    f="$HOME/.config/opencode/skills/${cmd}/SKILL.md"
    [[ -f "$f" ]] && rm -f "$f" && echo "  ✓ Removed ${f#$HOME/}" && removed=$((removed + 1))
  done

  echo ""
  if [[ $removed -eq 0 ]]; then
    echo "Nothing to remove — commands were not installed."
  else
    echo "Removed ${removed} file(s). Restart your IDE to apply."
  fi
}

# ── Main ─────────────────────────────────────────────────────────────

case "${1:-}" in
  --uninstall)  do_uninstall ;;
  --help|-h)
    echo "AI Workflow Wizard installer"
    echo ""
    echo "Usage:"
    echo "  bash install.sh            Install global commands + skills"
    echo "  bash install.sh --uninstall Remove global commands + skills"
    ;;
  *)  do_install ;;
esac
