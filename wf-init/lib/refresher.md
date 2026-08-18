# Refresh orchestrator — phases R-1 through R6

This file is read as instructions by the agent running `/wf-refresh`. **Do not `source` this Markdown file.** Execute each fenced bash block in order, pausing for user approval at Phase R5.

Prerequisites (set by `templates/commands/wf-refresh/_base.md`):
- `WF_DIR` is `/tmp/wf-refresh-phases` (or wherever the command downloaded the phase files).
- `WF_RAW` is `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`.
- `.wizard-state.json` exists in the current project directory.

---

## Setup: create helper library

Run this block first. It writes a pure bash helper library that every later phase sources.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
WF_STATE=".wizard-state.json"
WIZARD_REPO="${WIZARD_REPO:-hugoafj/ai-workflow-wizard}"
WIZARD_BRANCH="${WIZARD_BRANCH:-main}"
WF_RAW="${WF_RAW:-https://raw.githubusercontent.com/${WIZARD_REPO}/${WIZARD_BRANCH}}"

mkdir -p "${WF_DIR}/lib"

# Download the shared helpers so /wf-refresh and /wf-init use the same
# wf_fetch_version / wf_sha256 implementation. If the download fails, the
# heredoc below provides fallbacks.
curl -fsSL "${WF_RAW}/wf-init/lib/state-helpers.sh" -o "${WF_DIR}/lib/state-helpers.sh" 2>/dev/null || true

cat > "${WF_DIR}/lib/refresh-lib.sh" << 'LIBEOF'
#!/bin/bash
# Pure bash helper library for /wf-refresh.
# No Markdown files are sourced here.

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
WF_STATE="${WF_STATE:-.wizard-state.json}"
WIZARD_REPO="${WIZARD_REPO:-hugoafj/ai-workflow-wizard}"
WIZARD_BRANCH="${WIZARD_BRANCH:-main}"
WF_RAW="${WF_RAW:-https://raw.githubusercontent.com/${WIZARD_REPO}/${WIZARD_BRANCH}}"

# Source shared helpers (wf_fetch_version, wf_sha256) from /wf-init.
[ -f "${WF_DIR}/lib/state-helpers.sh" ] && source "${WF_DIR}/lib/state-helpers.sh"

# Fallback portable sha256 if the shared helper is unavailable.
if ! command -v wf_sha256 >/dev/null 2>&1; then
  wf_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum -- "$1" | awk '{print $1}'
    else
      shasum -a 256 -- "$1" | awk '{print $1}'
    fi
  }
fi

# Fallback version fetcher if the shared helper is unavailable.
if ! command -v wf_fetch_version >/dev/null 2>&1; then
  wf_fetch_version() {
    local version=""
    version=$(curl -fsSL "${WF_RAW}/VERSION" 2>/dev/null | head -1 || true)
    if [[ -z "$version" && -f VERSION ]]; then
      version=$(head -1 VERSION)
    fi
    if [[ -z "$version" ]]; then
      version=$(curl -fsSL "https://api.github.com/repos/${WIZARD_REPO}/releases/latest" 2>/dev/null | jq -r '.tag_name // empty' 2>/dev/null || true)
    fi
    if [[ -z "$version" ]]; then
      version=$(curl -fsSL "https://api.github.com/repos/${WIZARD_REPO}/tags?per_page=1" 2>/dev/null | jq -r '.[0].name // empty' 2>/dev/null || true)
    fi
    if [[ -z "$version" ]]; then
      version="0.7.1-beta.1"
    fi
    # Strip a leading 'v' BEFORE the emptiness check: VERSION="v" alone would
    # otherwise pass the -z check and printf an empty string.
    version="${version#v}"
    printf '%s' "${version:-0.7.1-beta.1}"
  }
fi

# Normalize a version: strip leading 'v'
_version_norm() {
  local v="$1"
  v="${v#v}"
  printf '%s' "$v"
}

# Compare two semver-like versions. Returns 0 if $1 <= $2, 1 otherwise.
# Supports x.y.z[-prerelease[.N]] where prerelease fields are '.'-separated.
# Release (no prerelease) is greater than any prerelease of the same MAJ.MIN.PATCH.
version_lte() {
  local LC_ALL
  LC_ALL=C
  export LC_ALL
  local v1 v2
  v1="$(_version_norm "$1")"
  v2="$(_version_norm "$2")"

  local m1 n1 p1 pre1 m2 n2 p2 pre2
  if [[ "$v1" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(-(.*))?$ ]]; then
    m1="${BASH_REMATCH[1]}"
    n1="${BASH_REMATCH[2]}"
    p1="${BASH_REMATCH[3]}"
    pre1="${BASH_REMATCH[5]}"
  else
    echo "version_lte: invalid version '$1'" >&2
    return 1
  fi

  if [[ "$v2" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(-(.*))?$ ]]; then
    m2="${BASH_REMATCH[1]}"
    n2="${BASH_REMATCH[2]}"
    p2="${BASH_REMATCH[3]}"
    pre2="${BASH_REMATCH[5]}"
  else
    echo "version_lte: invalid version '$2'" >&2
    return 1
  fi

  # Force base-10 arithmetic: components like "08" or "010" must not be
  # parsed as octal (which would error and mis-order versions).
  if (( 10#$m1 != 10#$m2 )); then
    (( 10#$m1 < 10#$m2 )) && return 0 || return 1
  fi
  if (( 10#$n1 != 10#$n2 )); then
    (( 10#$n1 < 10#$n2 )) && return 0 || return 1
  fi
  if (( 10#$p1 != 10#$p2 )); then
    (( 10#$p1 < 10#$p2 )) && return 0 || return 1
  fi

  # No pre-release on both -> equal -> lte true
  if [[ -z "$pre1" && -z "$pre2" ]]; then
    return 0
  fi

  # Release > prerelease
  if [[ -z "$pre1" && -n "$pre2" ]]; then
    return 1  # v1 is release, v2 is prerelease: v1 > v2
  fi
  if [[ -n "$pre1" && -z "$pre2" ]]; then
    return 0  # v1 is prerelease, v2 is release: v1 < v2
  fi

  # Both have pre-release fields; compare component by component
  IFS='.' read -ra pr1 <<< "$pre1"
  IFS='.' read -ra pr2 <<< "$pre2"

  local i x y
  for (( i=0; i<${#pr1[@]} || i<${#pr2[@]}; i++ )); do
    x="${pr1[i]:-}"
    y="${pr2[i]:-}"

    # Fewer fields means smaller pre-release (when all prior equal)
    if [[ -z "$x" && -n "$y" ]]; then
      return 0
    fi
    if [[ -n "$x" && -z "$y" ]]; then
      return 1
    fi

    if [[ "$x" =~ ^[0-9]+$ && "$y" =~ ^[0-9]+$ ]]; then
      if (( 10#$x < 10#$y )); then return 0; fi
      if (( 10#$x > 10#$y )); then return 1; fi
    elif [[ "$x" =~ ^[0-9]+$ ]]; then
      # x numeric, y non-numeric: numeric identifiers have lower precedence
      return 0
    elif [[ "$y" =~ ^[0-9]+$ ]]; then
      # y numeric, x non-numeric
      return 1
    else
      # Both non-numeric: ASCII sort
      if [[ "$x" < "$y" ]]; then return 0; fi
      if [[ "$x" > "$y" ]]; then return 1; fi
    fi
  done

  # Equal
  return 0
}

version_lt() {
  local v1="$1" v2="$2"
  # Normalize both operands BEFORE the equality check, so "v0.7.1" and "0.7.1"
  # compare equal and version_lt returns false (they are the same version).
  v1="$(_version_norm "$v1")"
  v2="$(_version_norm "$v2")"
  if [[ "$v1" == "$v2" ]]; then
    return 1
  fi
  version_lte "$v1" "$v2"
}

# Ask a yes/no question safely in BOTH tty and non-tty (agent-driven) contexts.
# In an interactive tty it prompts like a normal read -n 1. When stdin is EOF or
# not a tty (agent run), a bare `read` would fail under `set -e` and abort the
# script. In that case, respect WF_REFRESH_DEFAULT_ANSWER ("yes" or "no") if
# it is set; otherwise fail loudly instead of silently defaulting to NO.
_ask_yesno_safe() {
  local prompt="$1"
  local reply leftover
  if ! read -p "$prompt [y/n] " -n 1 -r reply 2>/dev/null; then
    if [ "${WF_REFRESH_DEFAULT_ANSWER:-}" = "yes" ]; then
      echo "(non-interactive — using WF_REFRESH_DEFAULT_ANSWER=yes)"
      return 0
    elif [ "${WF_REFRESH_DEFAULT_ANSWER:-}" = "no" ]; then
      echo "(non-interactive — using WF_REFRESH_DEFAULT_ANSWER=no)"
      return 1
    else
      echo "ERROR: non-interactive input required but WF_REFRESH_DEFAULT_ANSWER is not set." >&2
      echo "  Aborting: refusing to silently default to NO. Set WF_REFRESH_DEFAULT_ANSWER=yes|no to continue non-interactively." >&2
      exit 2
    fi
  fi
  echo
  # When stdin is piped (not a tty), `read -n 1` consumes only the first char and
  # leaves the rest of the line in the buffer; drain it so the leftover '\n' does
  # not corrupt the next question.
  if [[ ! -t 0 ]]; then
    read -r leftover 2>/dev/null || true
  fi
  if [[ "$reply" =~ ^[Yy]$ ]]; then
    return 0
  else
    return 1
  fi
}

# Ask a yes/no question. Returns 0 for yes, 1 for no.
_ask_yesno() {
  _ask_yesno_safe "$1"
}

# Apply a single state migration block idempotently using jq.
# Writes a .tmp file and moves it into place.
_apply_jq_filter() {
  local filter="${@: -1}"
  local args=()
  local tmp="${WF_STATE}.tmp"
  # zsh does NOT honor bash-style "$@" slicing ("${@:1:$#-1}" leaves the full
  # array), so pop every arg except the last (the filter) with a portable loop.
  # A single-argument call (filter only) falls straight through to the else.
  if [ $# -gt 1 ]; then
    while [ "$#" -gt 1 ]; do
      args+=("$1")
      shift
    done
    jq "${args[@]}" "$filter | .updated_at = (now | todate)" "$WF_STATE" > "$tmp" && mv "$tmp" "$WF_STATE"
  else
    jq "$filter | .updated_at = (now | todate)" "$WF_STATE" > "$tmp" && mv "$tmp" "$WF_STATE"
  fi
}

# Migrate state from CURRENT_VERSION to TARGET_VERSION.
# Schema migration ensures required fields exist. Feature defaults are NOT set
# here: Phase R2 asks the user about protocol features missing from .features
# (decision_ladder, tdd_protocol, routing_abc) using _ask_yesno_safe. Features
# already present in state are never re-asked.
migrate_state() {
  local CURRENT="$1"
  local TARGET="$2"

  if ! version_lt "$CURRENT" "$TARGET"; then
    echo "  No migration needed: $CURRENT already >= $TARGET"
    return 0
  fi

  echo "  Upgrading state from $CURRENT to $TARGET..."
  
  # Ensure schema v3 required fields exist (idempotent: //= creates only if missing).
  # Do NOT set default values for features here — Phase R2 asks instead.
  _apply_jq_filter '
    .schema_version = 3 |
    .wizard_version = "'"$TARGET"'" |
    .build_plan //= {} |
    .build_plan.managed_paths //= [] |
    .build_plan.generated_files //= [] |
    .build_plan.approval //= {} |
    .features //= {} |
    .ci //= {} |
    .ci.e2e_in_ci //= false |
    .ci.auto_improve //= true |
    .ci.inline_suggestions //= true
  '

  echo "  ✓ State upgraded from $CURRENT to $TARGET"
}

# Ensure custom AGENTS.md sections are preserved.
# Reads existing AGENTS.md, extracts blocks between markers, and re-injects them
# into the staged AGENTS.md at the same relative position (before the heading
# that originally followed each block). Blocks that are already present in the
# staged file are skipped so the function stays idempotent.
preserve_custom_agents() {
  local STAGING="${1:-.wizard-staging}"
  local PROJECT_AGENTS="AGENTS.md"
  local STAGED_AGENTS="${STAGING}/AGENTS.md"

  if [[ ! -f "$PROJECT_AGENTS" ]] || [[ ! -f "$STAGED_AGENTS" ]]; then
    return 0
  fi

  if ! grep -q "<!-- WF: DO NOT REGENERATE -->" "$PROJECT_AGENTS"; then
    return 0
  fi

  echo "  Preserving custom AGENTS.md sections..."

  local TMP="${STAGED_AGENTS}.tmp"
  local BLOCK_DIR="${STAGED_AGENTS}.blocks"
  rm -rf "$BLOCK_DIR"
  mkdir -p "$BLOCK_DIR"

  local -a ALL_LINES
  local LINE
  while IFS= read -r LINE || [[ -n "$LINE" ]]; do
    ALL_LINES+=("$LINE")
  done < "$PROJECT_AGENTS"
  local TOTAL=${#ALL_LINES[@]}

  local IN_CUSTOM=false
  local FOLLOWING=()
  local SIGNATURES=()
  local BLOCK_FILES=()
  local i=0 j=0

  for (( i=0; i<TOTAL; i++ )); do
    LINE="${ALL_LINES[$i]}"
    if $IN_CUSTOM; then
      printf '%s\n' "$LINE" >> "$BLOCK_DIR/block_$j"
      if [[ "$LINE" == *"<!-- /WF: DO NOT REGENERATE -->"* ]]; then
        IN_CUSTOM=false
        local FOLLOWING_H=""
        local k
        for (( k=i+1; k<TOTAL; k++ )); do
          if [[ "${ALL_LINES[$k]}" =~ ^##[[:space:]]+ ]]; then
            FOLLOWING_H="${ALL_LINES[$k]}"
            break
          fi
        done
        FOLLOWING+=("$FOLLOWING_H")
        SIGNATURES+=("$(sed -n '2,$p' "$BLOCK_DIR/block_$j" | sed '$d' | grep -m1 . || true)")
        BLOCK_FILES+=("$BLOCK_DIR/block_$j")
        j=$((j + 1))
      fi
      continue
    fi

    if [[ "$LINE" == *"<!-- WF: DO NOT REGENERATE -->"* ]]; then
      IN_CUSTOM=true
      printf '%s\n' "$LINE" > "$BLOCK_DIR/block_$j"
    fi
  done

  if [[ ${#BLOCK_FILES[@]} -eq 0 ]]; then
    rm -rf "$BLOCK_DIR"
    echo "  ℹ No custom sections found in $PROJECT_AGENTS"
    return 0
  fi

  local FOLLOWING_H SIG BF
  for (( j=0; j<${#BLOCK_FILES[@]}; j++ )); do
    BF="${BLOCK_FILES[$j]}"
    FOLLOWING_H="${FOLLOWING[$j]}"
    SIG="${SIGNATURES[$j]}"

    if [[ -n "$SIG" ]] && grep -qF -- "$SIG" "$STAGED_AGENTS"; then
      continue
    fi

    if [[ -n "$FOLLOWING_H" ]] && grep -qF -- "$FOLLOWING_H" "$STAGED_AGENTS"; then
      awk -v heading="$FOLLOWING_H" -v blockfile="$BF" '
        $0 == heading {
          print ""
          while ((getline line < blockfile) > 0) print line
          close(blockfile)
          print ""
          print
          inserted=1
          next
        }
        { print }
        END {
          if (!inserted) {
            print ""
            while ((getline line < blockfile) > 0) print line
            close(blockfile)
          }
        }
      ' "$STAGED_AGENTS" > "$TMP"
      mv "$TMP" "$STAGED_AGENTS"
    else
      local FOOTER_LINE
      FOOTER_LINE=$(grep -n '^<!-- wf-version:' "$STAGED_AGENTS" | tail -1 | cut -d: -f1 || true)
      if [[ -n "$FOOTER_LINE" ]]; then
        {
          head -n "$((FOOTER_LINE - 1))" "$STAGED_AGENTS"
          printf '\n'
          cat "$BF"
          printf '\n'
          tail -n "+$FOOTER_LINE" "$STAGED_AGENTS"
        } > "$TMP"
        mv "$TMP" "$STAGED_AGENTS"
      else
        {
          printf '\n'
          cat "$BF"
          printf '\n'
        } >> "$STAGED_AGENTS"
      fi
    fi
  done

  rm -rf "$BLOCK_DIR"
  rm -f "$TMP"
  echo "  ✓ Custom sections preserved"
}

# Reinsert the "Gentle AI — Legacy Path Bridge for Windsurf/Devin" rule into a
# target file when Windsurf/Devin is an active IDE. Mirrors phase8's safety net:
# the staging router does not carry the rule, so a refresh must re-add it.
# $1 (optional) is the target file to patch — defaults to AGENTS.md. In R6 the
# caller passes "$STAGING/AGENTS.md", so the bridge is inserted into the STAGED
# AGENTS.md before the approved copy is promoted (and only when AGENTS.md is
# approved). Idempotent: skips when the rule is already present (e.g. preserved
# via DO NOT REGENERATE markers or by a previous reinsert).
reinsert_legacy_bridge() {
  local IDES RULE_FILE TARGET
  IDES=$(jq -r '.answers.ides[]?' "$WF_STATE" 2>/dev/null)
  if ! echo "$IDES" | grep -q "windsurf"; then
    return 0
  fi
  RULE_FILE="${WF_DIR}/temp-files/AGENTS.md"
  TARGET="${1:-AGENTS.md}"
  if [ ! -f "$RULE_FILE" ] || [ ! -f "$TARGET" ]; then
    return 0
  fi
  if grep -q "Gentle AI — Legacy Path Bridge" "$TARGET"; then
    echo "  ℹ Legacy path bridge already present in $TARGET"
    return 0
  fi
  # AGENTS.router.md may begin with leading HTML comments; find the first
  # markdown heading ("# ") and insert after it. head/cat/tail are portable on
  # BOTH BSD (macOS) and GNU (Linux) coreutils.
  # Wrap in DO NOT REGENERATE markers so future refreshes preserve it.
  # temp-files/AGENTS.md has no trailing newline, so add one before the
  # closing marker to keep it on its own line.
  TITLE_LINE=$(grep -n '^# ' "$TARGET" | head -1 | cut -d: -f1)
  if [ -z "$TITLE_LINE" ]; then
    echo "  ⚠ Could not find $TARGET title line for Windsurf bridge injection; skipping." >&2
    return 0
  fi
  {
    head -n "$TITLE_LINE" "$TARGET"
    printf '%s\n' "<!-- WF: DO NOT REGENERATE -->"
    cat "$RULE_FILE"
    printf '\n%s\n' "<!-- /WF: DO NOT REGENERATE -->"
    tail -n +$((TITLE_LINE + 1)) "$TARGET"
  } > "$TARGET.tmp"
  mv "$TARGET.tmp" "$TARGET"
  if grep -q "Gentle AI — Legacy Path Bridge" "$TARGET"; then
    echo "  ✓ Windsurf legacy path bridge rule reinserted into $TARGET"
  else
    echo "  ⚠ Windsurf legacy path bridge rule MISSING from $TARGET after reinsert." >&2
  fi
}

LIBEOF

chmod +x "${WF_DIR}/lib/refresh-lib.sh"
echo "✓ Helper library written to ${WF_DIR}/lib/refresh-lib.sh"
```

---

## Phase R-1: Global command refresh

Check whether the global commands (`wf-init`, `wf-refresh`, `wf-cleanup`) are up-to-date. If the local wizard version is behind the remote `VERSION` file, offer to run `install.sh`.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

LOCAL_VERSION=""
# install.sh SIEMPRE instala en .agents/skills/ (unconditional fallback universal)
UNIVERSAL_SKILL="$HOME/.agents/skills/wf-refresh/SKILL.md"
if [[ -f "$UNIVERSAL_SKILL" ]]; then
  LOCAL_VERSION=$(sed -n 's/^version: *\([^ ]*\).*/\1/p' "$UNIVERSAL_SKILL" | head -1)
fi
# Fallback a state solo si no existe (primer run sin install.sh)
if [[ -z "$LOCAL_VERSION" ]]; then
  LOCAL_VERSION=$(jq -r '.wizard_version // empty' "$WF_STATE" 2>/dev/null || true)
fi
LOCAL_VERSION="${LOCAL_VERSION:-0.7.1-beta.1}"
LOCAL_VERSION="${LOCAL_VERSION#v}"

echo "ℹ Local wizard version: $LOCAL_VERSION"

REMOTE_VERSION=$(curl -fsSL "${WF_RAW}/VERSION" 2>/dev/null | head -1 || true)
REMOTE_VERSION="${REMOTE_VERSION:-$(wf_fetch_version)}"
REMOTE_VERSION="${REMOTE_VERSION#v}"

if [[ -z "$REMOTE_VERSION" ]]; then
  echo "⚠ Could not fetch remote version (network issue?)"
  echo "  Continuing with local version: $LOCAL_VERSION"
  exit 0
fi

echo "ℹ Remote wizard version: $REMOTE_VERSION"

if [[ "$LOCAL_VERSION" == "$REMOTE_VERSION" ]]; then
  echo "✓ Wizard is up-to-date"
  exit 0
fi

if version_lt "$LOCAL_VERSION" "$REMOTE_VERSION"; then
  echo "⚠ Wizard is outdated (local: $LOCAL_VERSION, remote: $REMOTE_VERSION)"
  if _ask_yesno_safe "Update global commands?"; then
    # install.sh lives in the wizard repo, not in the project directory.
    INSTALL_SH="${WF_DIR}/install.sh"
    if curl -fsSL "${WF_RAW}/install.sh" -o "$INSTALL_SH" 2>/dev/null && [[ -s "$INSTALL_SH" ]]; then
      echo "ℹ Running install.sh..."
      bash "$INSTALL_SH" || echo "⚠ install.sh failed; continuing anyway"
    else
      echo "⚠ Could not download install.sh from ${WF_RAW}/install.sh; skipping update"
    fi
  else
    echo "ℹ Skipping update; you can run install.sh manually later"
  fi
else
  echo "⚠ Local version is ahead of remote (local: $LOCAL_VERSION, remote: $REMOTE_VERSION)"
fi

echo "✓ Phase R-1 complete"
```

---

## Phase R0: Project validation

Validate `.wizard-state.json` and detect active IDEs.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

if [[ ! -f "$WF_STATE" ]]; then
  echo "✗ $WF_STATE not found"
  echo "  Please run /wf-init first"
  exit 1
fi

if ! jq empty "$WF_STATE" 2>/dev/null; then
  echo "✗ $WF_STATE is not valid JSON"
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "✗ Not a git repository"
  exit 1
fi

# SKILL Phase 0 pre-checks (informational; do not block by default).
if [[ ! -f AGENTS.md ]]; then
  echo "⚠ No AGENTS.md found — /wf-refresh targets this file; run /wf-init first for a full setup"
fi
if [[ -f AGENTS.md ]] && ! grep -q 'wf-version:' AGENTS.md; then
  echo "⚠ AGENTS.md has no 'wf-version:' footer — it may not be wizard-managed"
fi
if command -v gentle-ai >/dev/null 2>&1; then
  if ! gentle-ai doctor >/dev/null 2>&1; then
    echo "⚠ 'gentle-ai doctor' reported issues — review the Gentle AI runtime before relying on its gates"
  fi
fi
if [[ -d openspec ]] && [[ ! -d openspec/changes ]]; then
  echo "⚠ openspec/ exists but openspec/changes/ is missing — SDD pre-check may fail later"
fi

SCHEMA_VERSION=$(jq -r '.schema_version // 0' "$WF_STATE")
if [[ "$SCHEMA_VERSION" -lt 3 ]]; then
  echo "✗ State schema is too old (v$SCHEMA_VERSION < v3)"
  echo "  Phase R2 will migrate the schema. Continuing."
fi

echo "✓ State validation passed (schema v$SCHEMA_VERSION)"

IDES=()
[[ -d .claude ]] && IDES+=("claude-code")
[[ -d .cursor ]] && IDES+=("cursor")
if [[ -d .windsurf ]] || [[ -d .devin ]]; then
  IDES+=("windsurf")
fi
[[ -d .kiro ]] && IDES+=("kiro")
[[ -d .codex ]] && IDES+=("codex")
[[ -d .opencode ]] && IDES+=("opencode")
if [[ -d .gemini ]] || [[ -f GEMINI.md ]]; then
  IDES+=("gemini-cli")
fi
if [[ -d .antigravity ]] || [[ -f ANTIGRAVITY.md ]]; then
  IDES+=("antigravity")
fi
[[ -f .github/copilot-instructions.md ]] && IDES+=("vscode-copilot")

if [[ ${#IDES[@]} -eq 0 ]]; then
  echo "⚠ No active IDEs detected"
else
  echo "ℹ Detected IDEs: ${IDES[*]}"
fi

if [[ ${#IDES[@]} -eq 0 ]]; then
  IDES_JSON='[]'
else
  IDES_JSON=$(printf '%s\n' "${IDES[@]}" | jq -R . | jq -s .)
fi
# Merge detected IDEs with the existing answers instead of overwriting them:
# a previously configured IDE whose directory is temporarily absent must not be
# dropped (its generated files would then be offered for deletion as unmanaged).
_apply_jq_filter --argjson ides "$IDES_JSON" '.answers.ides = ((.answers.ides // []) + $ides | unique)'

echo "✓ Phase R0 complete"
```

---

## Phase R1: Project content drift

Re-discover the project to detect changes in structure, dependencies, conventions.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

echo "ℹ Re-discovering project..."

STACK_KEY="unknown"
if [[ -f package.json ]]; then
  STACK_KEY="node-react"
  if command -v jq >/dev/null 2>&1; then
    # Read the package NAME (key), not the version value: .dependencies.next
    # returns "^14.0.0", which would produce a bogus "node-^14.0.0" key.
    pkg_framework=$(jq -r '.dependencies | keys[] | select(. == "next" or . == "vue") | .' package.json 2>/dev/null | head -1 || true)
    [[ -n "$pkg_framework" ]] && STACK_KEY="node-${pkg_framework}"
  fi
elif [[ -f composer.json ]]; then
  STACK_KEY="php-laravel"
elif [[ -f pyproject.toml ]]; then
  STACK_KEY="python-django"
fi

NODE_ENGINE=""
if [[ -f package.json ]] && command -v node >/dev/null 2>&1; then
  NODE_ENGINE=$(node -e "try { process.stdout.write(require('./package.json').engines?.node||'') } catch {}" 2>/dev/null || true)
fi

NPM_MAJOR=""
if command -v npm >/dev/null 2>&1; then
  NPM_MAJOR=$(npm --version 2>/dev/null | cut -d. -f1 || true)
fi

GIT_COMMITS=$(git log --oneline 2>/dev/null | wc -l | tr -d '[:space:]' || echo "0")

OLD_STACK=$(jq -r '.discovery.stack.stack_key // .discovery.stack_key // ""' "$WF_STATE")
OLD_NODE=$(jq -r '.discovery.node_engine // ""' "$WF_STATE")
OLD_NPM=$(jq -r '.discovery.npm_major // ""' "$WF_STATE")

if [[ "$OLD_STACK" != "$STACK_KEY" ]] || [[ "$OLD_NODE" != "$NODE_ENGINE" ]] || [[ "$OLD_NPM" != "$NPM_MAJOR" ]]; then
  echo "⚠ Project content drift detected:"
  [[ "$OLD_STACK" != "$STACK_KEY" ]] && echo "  - Stack: $OLD_STACK → $STACK_KEY"
  [[ "$OLD_NODE" != "$NODE_ENGINE" ]] && echo "  - Node engine: $OLD_NODE → $NODE_ENGINE"
  [[ "$OLD_NPM" != "$NPM_MAJOR" ]] && echo "  - npm major: $OLD_NPM → $NPM_MAJOR"

  if _ask_yesno_safe "Use updated project info?"; then
_apply_jq_filter \
  --arg stack_key "$STACK_KEY" \
  --arg node_engine "$NODE_ENGINE" \
  --arg npm_major "$NPM_MAJOR" \
  --argjson git_commits "$GIT_COMMITS" \
  '.discovery.stack.stack_key = $stack_key | .discovery.node_engine = $node_engine | .discovery.npm_major = $npm_major | .discovery.git_commits = $git_commits'
    echo "✓ Updated discovery fields"
  else
    echo "ℹ Keeping existing discovery fields"
  fi
else
  echo "✓ No project drift detected"
fi

echo "✓ Phase R1 complete"
```

---

## Phase R2: State/schema migration

Migrate `.wizard-state.json` from its current version to the actual `TARGET_VERSION` using cumulative, semver-aware migrations.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

echo "ℹ Checking for state migrations..."

CURRENT_VERSION=$(jq -r '.wizard_version // "0.0.0"' "$WF_STATE")
CURRENT_VERSION="${CURRENT_VERSION#v}"

TARGET_VERSION=$(wf_fetch_version)
TARGET_VERSION="${TARGET_VERSION#v}"

echo "ℹ Current state version: $CURRENT_VERSION"
echo "ℹ Target version: $TARGET_VERSION"

migrate_state "$CURRENT_VERSION" "$TARGET_VERSION"

# Ask about new optional protocol features that are not present in the local
# state yet (features added by newer wizard versions). ci/cd/release_please are
# NOT asked here: they require the full phase47-cicd questionnaire and are
# configured via /wf-settings or /wf-init. Disabled features are recorded
# explicitly so they are never re-asked.
for FEATURE in decision_ladder tdd_protocol routing_abc; do
  if ! jq -e ".features.$FEATURE != null" "$WF_STATE" >/dev/null 2>&1; then
    echo "New optional feature available: $FEATURE"
    if _ask_yesno_safe "Enable $FEATURE?"; then
      jq ".features.$FEATURE = true | .updated_at = (now | todate)" "$WF_STATE" > "$WF_STATE.tmp" && mv "$WF_STATE.tmp" "$WF_STATE"
      echo "✓ $FEATURE enabled"
    else
      jq ".features.$FEATURE = false | .updated_at = (now | todate)" "$WF_STATE" > "$WF_STATE.tmp" && mv "$WF_STATE.tmp" "$WF_STATE"
      echo "✗ $FEATURE disabled"
    fi
  fi
done

echo "✓ Phase R2 complete"
```

---

## Phase R3: Build new staging

Re-run the Builder (B1-B9) to generate all artifacts into `.wizard-staging/`.

**Step 0 — Snapshot the current managed files (MUST run before delegating the Builder).**

The Builder overwrites `state.build_plan.generated_files` / `managed_paths` with the NEW
staging set (B9/B9.5). To detect deletions in R4, the pre-Builder baseline must be captured
first. Run this block before delegating Builder-Core:

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

BASELINE=".wizard-refresh-baseline.json"
jq '{managed_paths: (.build_plan.managed_paths // []), generated_files: (.build_plan.generated_files // [])}' "$WF_STATE" > "$BASELINE"
echo "✓ Baseline snapshot written ($(jq '.managed_paths | length' "$BASELINE") managed paths)"
```

**Instructions for the agent:**

1. Use the same Builder sub-agent delegation as `/wf-init` Phase 6:
   - Read `phase6a-agents.md` first. If your environment supports it (e.g. Claude Code `task` tool, Devin `run_subagent` tool), delegate Builder-Core to a sub-agent with the prompt from `subagent-builder-core.md`.
   - When replacing placeholders in the sub-agent prompt, use:
     - `{WF_PATH}` → `$WF_DIR` (the downloaded phase directory, e.g. `/tmp/wf-refresh-phases`)
     - `{WF_RAW}` → `https://raw.githubusercontent.com/${WIZARD_REPO}/${WIZARD_BRANCH}`
     - `{PROJECT_PATH}` → the current working directory
     - `{WF_STAGING}` → the staging directory (`$STAGING` or `{PROJECT_PATH}/.wizard-staging`)
     - `{WF_STATE}` → `.wizard-state.json`
   - The helper `lib/state-helpers.sh` lives directly under `$WF_DIR/lib/`.
   - Otherwise, read `lib/builder.md` and execute B1-B6 manually.
2. After Builder-Core completes, read `phase6b-build-heavy.md` and run Builder-Heavy (B7-B9) the same way — **execute ONLY its steps 1-4 (verify staging, delegate, fallback, validate). Do NOT execute phase6b's Step 5 tail**: no `wf_phase_done phase6 phase7`, no "Wait for user confirmation", and NO `cat "$WF_DIR/phase7.md"`. Those belong to the `/wf-init` phase 7/8 flow, not to refresh — running them would derail into wf-init's review/promotion instead of returning to Phase R4. If you invoke `phase6b-build-heavy.md` through a bash wrapper, set `WF_REFRESH=1` so Step 5 guards the phase7 promotion. After Builder-Heavy validates, return to Phase R4 below.
3. The combined result must be `.wizard-staging/` containing `AGENTS.md`, the satellite files, commands, protocols, etc.
4. After Builder finishes, run the validation block below.

> **Important:** `lib/refresher.md`, `lib/builder.md`, `phase6a-agents.md`, and `phase6b-build-heavy.md` are **Markdown instruction files**, not bash scripts. Do not `source` them.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")

if [[ ! -d "$STAGING" ]]; then
  echo "✗ $STAGING/ was not created."
  echo "  Builder (Phase R3) did not complete successfully."
  exit 1
fi

echo "=== Staging files ==="
find "$STAGING" -type f | sort
echo ""

echo "$(find "$STAGING" -type f | wc -l) files in $STAGING/"

# .wizard-state.json intentionally NOT validated in staging: state lives at the
# project root; staging holds only generated files.
for artifact in AGENTS.md; do
  if [[ ! -f "$STAGING/$artifact" ]]; then
    echo "✗ Missing critical artifact: $STAGING/$artifact"
    exit 1
  fi
done

# The R4 deletion diff depends on the pre-Builder snapshot from Step 0.
if [[ ! -f .wizard-refresh-baseline.json ]]; then
  echo "✗ Baseline snapshot missing — run the Phase R3 Step 0 block before delegating the Builder."
  exit 1
fi

# Preserve custom AGENTS.md sections and reinsert the Windsurf/Devin legacy bridge
# into staged AGENTS.md now so R4's diff preview reflects the final content.
if [[ -f AGENTS.md ]] && [[ -f "$STAGING/AGENTS.md" ]]; then
  preserve_custom_agents "$STAGING"
fi
if [[ -f "$STAGING/AGENTS.md" ]]; then
  reinsert_legacy_bridge "$STAGING/AGENTS.md"
fi

echo "✓ Phase R3 validation passed"
```

---

## Phase R4: Diff and plan

Compare staging with the project. Classify each file as `added`, `updated`, `deleted`, `deleted_modified`, or `unchanged`.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")
PLAN="refresh-plan.json"

echo "ℹ Computing diff..."

ADDED="[]"
UPDATED="[]"
DELETED="[]"
DELETED_MODIFIED="[]"
UNCHANGED="[]"

# Scan staging files (null-delimited: paths with spaces are safe)
while IFS= read -r -d '' file; do
  REL_PATH="${file#$STAGING/}"
  STAGING_HASH=$(wf_sha256 "$file")

  if [[ -f "$REL_PATH" ]]; then
    PROJECT_HASH=$(wf_sha256 "$REL_PATH")
    if [[ "$STAGING_HASH" == "$PROJECT_HASH" ]]; then
      UNCHANGED=$(jq --arg path "$REL_PATH" --arg hash "$STAGING_HASH" '. += [{"path": $path, "hash": $hash}]' <<< "$UNCHANGED")
    else
      UPDATED=$(jq --arg path "$REL_PATH" --arg old_hash "$PROJECT_HASH" --arg new_hash "$STAGING_HASH" '. += [{"path": $path, "old_hash": $old_hash, "new_hash": $new_hash}]' <<< "$UPDATED")
    fi
  else
    ADDED=$(jq --arg path "$REL_PATH" --arg hash "$STAGING_HASH" '. += [{"path": $path, "hash": $hash}]' <<< "$ADDED")
  fi
# Exclude git-internal files from the plan, with one exception: .git/hooks/post-commit
# is staged by the builder for non-Husky projects. Git refuses to commit paths inside
# .git/, but the refresh still must copy/chmod the hook and track it as a managed
# side-effect. The git-add/commit filters below already skip .git/ paths.
done < <(
  find "$STAGING" -type f -not -path "*/.git/*" -print0
  if [[ -f "$STAGING/.git/hooks/post-commit" ]]; then
    printf '%s\0' "$STAGING/.git/hooks/post-commit"
  fi
)

# Deletion baseline: the R3 Step 0 snapshot (pre-Builder). Fall back to the live
# state only when the snapshot is missing (e.g. running R4 standalone). Normalize
# both sources to expose managed_paths and generated_files at the top level.
BASELINE=".wizard-refresh-baseline.json"
OLD_MANAGED=$(mktemp)
if [[ -f "$BASELINE" ]]; then
  jq '{managed_paths: (.managed_paths // []), generated_files: (.generated_files // [])}' "$BASELINE" > "$OLD_MANAGED"
else
  jq '{managed_paths: (.build_plan.managed_paths // []), generated_files: (.build_plan.generated_files // [])}' "$WF_STATE" > "$OLD_MANAGED"
fi

# Scan old managed paths for deletions (null-delimited for paths with spaces/newlines).
while IFS= read -r -d '' old_path; do
  # Never treat git-internal files as wizard-managed (defense in depth: older
  # plans may have recorded .git/ paths before the R4 find exclusion).
  if [[ "$old_path" == .git ]] || [[ "$old_path" == .git/* ]]; then
    continue
  fi
  if [[ ! -f "$STAGING/$old_path" ]]; then
    if [[ -f "$old_path" ]]; then
      PROJECT_HASH=$(wf_sha256 "$old_path")
      OLD_HASH=$(jq -r --arg path "$old_path" '.generated_files[] | select(.path == $path) | .hash' "$OLD_MANAGED" 2>/dev/null || true)

      if [[ -z "$OLD_HASH" ]]; then
        # No recorded hash (e.g. migrated plans with empty generated_files):
        # we cannot prove the user did NOT modify it, so require explicit
        # approval instead of silently classifying as plain deleted.
        DELETED_MODIFIED=$(jq --arg path "$old_path" --arg old_hash "" --arg project_hash "$PROJECT_HASH" '. += [{"path": $path, "old_hash": $old_hash, "project_hash": $project_hash, "reason": "deprecated (no recorded hash — user may have modified)"}]' <<< "$DELETED_MODIFIED")
      elif [[ "$PROJECT_HASH" == "$OLD_HASH" ]]; then
        DELETED=$(jq --arg path "$old_path" --arg hash "$PROJECT_HASH" '. += [{"path": $path, "hash": $hash, "reason": "deprecated"}]' <<< "$DELETED")
      else
        DELETED_MODIFIED=$(jq --arg path "$old_path" --arg old_hash "$OLD_HASH" --arg project_hash "$PROJECT_HASH" '. += [{"path": $path, "old_hash": $old_hash, "project_hash": $project_hash, "reason": "deprecated (user modified)"}]' <<< "$DELETED_MODIFIED")
      fi
    fi
  fi
done < <(jq -j '.managed_paths[]? + "\u0000"' "$OLD_MANAGED" 2>/dev/null || true)
rm -f "$OLD_MANAGED"

# Write plan
jq -n \
  --argjson added "$ADDED" \
  --argjson updated "$UPDATED" \
  --argjson deleted "$DELETED" \
  --argjson deleted_modified "$DELETED_MODIFIED" \
  --argjson unchanged "$UNCHANGED" \
  '{added: $added, updated: $updated, deleted: $deleted, deleted_modified: $deleted_modified, unchanged: $unchanged}' > "$PLAN"

ADDED_COUNT=$(jq '.added | length' "$PLAN")
UPDATED_COUNT=$(jq '.updated | length' "$PLAN")
DELETED_COUNT=$(jq '.deleted | length' "$PLAN")
DELETED_MODIFIED_COUNT=$(jq '.deleted_modified | length' "$PLAN")
UNCHANGED_COUNT=$(jq '.unchanged | length' "$PLAN")

echo "ℹ Diff summary:"
echo "  Added: $ADDED_COUNT"
echo "  Updated: $UPDATED_COUNT"
echo "  Deleted: $DELETED_COUNT"
echo "  Deleted-modified: $DELETED_MODIFIED_COUNT (requires explicit approval)"
echo "  Unchanged: $UNCHANGED_COUNT (skipped)"

# The plan now holds the classified diff; the pre-Builder baseline is no longer
# needed. (R6's cleanup trap also removes it defensively.)
rm -f "$BASELINE"

echo "✓ Phase R4 complete"
```

---

## Phase R5: Review gate

Present the grouped diff and collect explicit user approvals for each category. Do NOT proceed to Phase R6 without approval.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

PLAN="refresh-plan.json"
STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")

echo ""
echo "=== REFRESH PLAN ==="
echo ""

ADDED_COUNT=$(jq '.added | length' "$PLAN")
if [[ $ADDED_COUNT -gt 0 ]]; then
  echo "📝 ADDED FILES ($ADDED_COUNT):"
  jq -r '.added[] | "  - \(.path)"' "$PLAN"
  echo ""
fi

UPDATED_COUNT=$(jq '.updated | length' "$PLAN")
if [[ $UPDATED_COUNT -gt 0 ]]; then
  echo "✏️  UPDATED FILES ($UPDATED_COUNT):"
  jq -r '.updated[] | "  - \(.path)"' "$PLAN"
  echo ""
fi

DELETED_COUNT=$(jq '.deleted | length' "$PLAN")
if [[ $DELETED_COUNT -gt 0 ]]; then
  echo "🗑️  DELETED FILES ($DELETED_COUNT):"
  jq -r '.deleted[] | "  - \(.path) (\(.reason))"' "$PLAN"
  echo ""
fi

DELETED_MODIFIED_COUNT=$(jq '.deleted_modified | length' "$PLAN")
if [[ $DELETED_MODIFIED_COUNT -gt 0 ]]; then
  echo "⚠️  DELETED-MODIFIED FILES ($DELETED_MODIFIED_COUNT) — user edited since last refresh:"
  jq -r '.deleted_modified[] | "  - \(.path) (\(.reason))"' "$PLAN"
  echo ""
fi

# Show the REAL diff before asking for approval (AGENTS.md: show me the full
# diff and wait for my approval). Preview each category with bounded output:
# added → staged content; updated → diff against staging; deleted/deleted_modified → current content.
MAX_PREVIEW_LINES="${MAX_PREVIEW_LINES:-120}"
_preview_file() {
  local label="$1" file="$2"
  echo "    --- $label: $file ---"
  if [[ "$label" == "UPDATED" ]]; then
    if diff -u "$file" "$STAGING/$file" 2>/dev/null | head -n "$MAX_PREVIEW_LINES"; then
      :
    else
      true
    fi
  elif [[ "$label" == "ADDED" ]]; then
    if head -n "$MAX_PREVIEW_LINES" "$STAGING/$file" 2>/dev/null; then :; fi
  else
    if head -n "$MAX_PREVIEW_LINES" "$file" 2>/dev/null; then :; fi
  fi
  echo ""
}

if [[ $ADDED_COUNT -gt 0 ]]; then
  echo "  Previewing ADDED files (first $MAX_PREVIEW_LINES lines each):"
  while IFS= read -r file; do
    _preview_file "ADDED" "$file"
  done < <(jq -r '.added[]?.path' "$PLAN")
fi

if [[ $UPDATED_COUNT -gt 0 ]]; then
  echo "  Previewing UPDATED files (diff vs staging, first $MAX_PREVIEW_LINES lines each):"
  while IFS= read -r file; do
    _preview_file "UPDATED" "$file"
  done < <(jq -r '.updated[]?.path' "$PLAN")
fi

if [[ $DELETED_COUNT -gt 0 ]]; then
  echo "  Previewing DELETED files (current content that would be removed, first $MAX_PREVIEW_LINES lines each):"
  while IFS= read -r file; do
    _preview_file "DELETED" "$file"
  done < <(jq -r '.deleted[]?.path' "$PLAN")
fi

if [[ $DELETED_MODIFIED_COUNT -gt 0 ]]; then
  echo "  Previewing DELETED-MODIFIED files (your local content that would be removed, first $MAX_PREVIEW_LINES lines each):"
  while IFS= read -r file; do
    _preview_file "DELETED-MODIFIED" "$file"
  done < <(jq -r '.deleted_modified[]?.path' "$PLAN")
fi

APPROVE_ADDED="false"
APPROVE_UPDATED="false"
APPROVE_DELETED="false"
APPROVE_DELETED_MODIFIED="false"

if [[ $ADDED_COUNT -gt 0 ]]; then
  if _ask_yesno_safe "Apply added files?"; then APPROVE_ADDED="true"; fi
fi

if [[ $UPDATED_COUNT -gt 0 ]]; then
  if _ask_yesno_safe "Apply updated files?"; then APPROVE_UPDATED="true"; fi
fi

if [[ $DELETED_COUNT -gt 0 ]]; then
  if _ask_yesno_safe "Delete removed files?"; then APPROVE_DELETED="true"; fi
fi

if [[ $DELETED_MODIFIED_COUNT -gt 0 ]]; then
  echo "The following files are wizard-managed but were modified by you."
  echo "Deleting them may lose your changes."
  jq -r '.deleted_modified[] | "  - \(.path)"' "$PLAN"
  if _ask_yesno_safe "Delete these modified files?"; then APPROVE_DELETED_MODIFIED="true"; fi
fi

# The refresh appends wizard-managed entries to .gitignore in R6. Mutating it
# behind the review gate contradicts AGENTS.md ("show me the full diff and wait
# for my approval"), so preview the exact lines that would be appended and
# require an explicit separate approval here.
GI_PROPOSED_LINES=(".wizard-managed-files.json" "!.agents/")
while IFS= read -r ide; do
  case "$ide" in
    claude-code) GI_PROPOSED_LINES+=("!.claude/") ;;
    cursor) GI_PROPOSED_LINES+=("!.cursor/") ;;
    windsurf) GI_PROPOSED_LINES+=("!.windsurf/" "!.devin/") ;;
    kiro) GI_PROPOSED_LINES+=("!.kiro/") ;;
    codex) GI_PROPOSED_LINES+=("!.codex/") ;;
    gemini-cli) GI_PROPOSED_LINES+=("!.gemini/" "!GEMINI.md") ;;
    antigravity) GI_PROPOSED_LINES+=("!ANTIGRAVITY.md") ;;
    opencode) GI_PROPOSED_LINES+=("!.opencode/") ;;
    vscode-copilot) GI_PROPOSED_LINES+=("!.github/copilot-instructions.md" "!.github/prompts/") ;;
  esac
done < <(jq -r '.answers.ides[]?' "$WF_STATE" 2>/dev/null)

MISSING_GI_LINES=()
for line in "${GI_PROPOSED_LINES[@]}"; do
  if ! grep -qxF "$line" .gitignore 2>/dev/null; then
    MISSING_GI_LINES+=("$line")
  fi
done

APPROVE_GITIGNORE="false"
if [[ ${#MISSING_GI_LINES[@]} -gt 0 ]]; then
  echo ""
  echo "🛡️  .gitignore changes (wizard-managed entries to be appended and committed):"
  printf '    + %s\n' "${MISSING_GI_LINES[@]}"
  echo ""
  if _ask_yesno_safe "Append these .gitignore entries and include them in the commit?"; then APPROVE_GITIGNORE="true"; fi
fi

# Store approvals in state
jq --argjson added "$APPROVE_ADDED" \
   --argjson updated "$APPROVE_UPDATED" \
   --argjson deleted "$APPROVE_DELETED" \
   --argjson deleted_modified "$APPROVE_DELETED_MODIFIED" \
   --argjson gitignore "$APPROVE_GITIGNORE" \
   '.build_plan.approval = {added: $added, updated: $updated, deleted: $deleted, deleted_modified: $deleted_modified, gitignore: $gitignore} | .updated_at = (now | todate)' "$WF_STATE" > "$WF_STATE.tmp"
mv "$WF_STATE.tmp" "$WF_STATE"

echo "✓ Phase R5 complete"
```

---

## Phase R6: Apply and close

Copy approved changes, update state, write `.wizard-managed-files.json`, commit, and clean staging.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")
PLAN="refresh-plan.json"

# Ensure staging, plan, and the R3 baseline are removed even if R6 fails.
cleanup_r6() {
  rm -rf "$STAGING"
  rm -f "$PLAN"
  rm -f .wizard-refresh-baseline.json
}
trap cleanup_r6 EXIT

echo "ℹ Applying approved changes..."

APPROVE_ADDED=$(jq -r '.build_plan.approval.added // false' "$WF_STATE")
APPROVE_UPDATED=$(jq -r '.build_plan.approval.updated // false' "$WF_STATE")
APPROVE_DELETED=$(jq -r '.build_plan.approval.deleted // false' "$WF_STATE")
APPROVE_DELETED_MODIFIED=$(jq -r '.build_plan.approval.deleted_modified // false' "$WF_STATE")
APPROVE_GITIGNORE=$(jq -r '.build_plan.approval.gitignore // false' "$WF_STATE")

# Preserve custom AGENTS.md sections BEFORE any copy: the project AGENTS.md still
# holds the user's custom markers here, and the staged AGENTS.md is the freshly
# generated plain version. If this ran after the copy loops, the project file
# would already be overwritten and preservation would silently no-op.
if [[ "$APPROVE_UPDATED" == "true" ]] || [[ "$APPROVE_ADDED" == "true" ]]; then
  if [[ -f AGENTS.md ]] && [[ -f "$STAGING/AGENTS.md" ]]; then
    preserve_custom_agents "$STAGING"
  fi
  # Reinsert the Windsurf/Devin legacy path bridge into the STAGED AGENTS.md so
  # the approved copy carries it, the manifest hashes it, and a declined refresh
  # writes nothing. Idempotent: skipped when the rule is already present (e.g.
  # preserved via DO NOT REGENERATE markers).
  if [[ -f "$STAGING/AGENTS.md" ]]; then
    reinsert_legacy_bridge "$STAGING/AGENTS.md"
  fi
fi

if [[ "$APPROVE_ADDED" == "true" ]]; then
  echo "ℹ Copying added files..."
  while IFS= read -r -d '' file; do
    mkdir -p "$(dirname "$file")"
    cp "$STAGING/$file" "$file"
    [[ "$file" == *".sh" ]] && chmod +x "$file"
    [[ "$file" == .husky/* || "$file" == .git/hooks/* ]] && chmod +x "$file"
  done < <(jq -j '.added[]?.path + "\u0000"' "$PLAN")
  echo "✓ Added files copied"
fi

if [[ "$APPROVE_UPDATED" == "true" ]]; then
  echo "ℹ Updating files..."
  while IFS= read -r -d '' file; do
    cp "$STAGING/$file" "$file"
    [[ "$file" == *".sh" ]] && chmod +x "$file"
    [[ "$file" == .husky/* || "$file" == .git/hooks/* ]] && chmod +x "$file"
  done < <(jq -j '.updated[]?.path + "\u0000"' "$PLAN")
  echo "✓ Files updated"
fi

if [[ "$APPROVE_DELETED" == "true" ]]; then
  echo "ℹ Deleting removed files..."
  DELETED_LIST=$(mktemp)
  jq -j '.deleted[]?.path + "\u0000"' "$PLAN" > "$DELETED_LIST"
  if [ -s "$DELETED_LIST" ]; then
    git rm -f --ignore-unmatch --pathspec-from-file="$DELETED_LIST" --pathspec-file-nul
  fi
  rm -f "$DELETED_LIST"
  echo "✓ Files deleted"
fi

if [[ "$APPROVE_DELETED_MODIFIED" == "true" ]]; then
  echo "ℹ Deleting modified-removed files..."
  DELETED_MODIFIED_LIST=$(mktemp)
  jq -j '.deleted_modified[]?.path + "\u0000"' "$PLAN" > "$DELETED_MODIFIED_LIST"
  if [ -s "$DELETED_MODIFIED_LIST" ]; then
    git rm -f --ignore-unmatch --pathspec-from-file="$DELETED_MODIFIED_LIST" --pathspec-file-nul
  fi
  rm -f "$DELETED_MODIFIED_LIST"
  echo "✓ Modified-removed files deleted"
fi

# Git operations (only if any category was approved)
if [[ "$APPROVE_ADDED" == "true" ]] || [[ "$APPROVE_UPDATED" == "true" ]] || [[ "$APPROVE_DELETED" == "true" ]] || [[ "$APPROVE_DELETED_MODIFIED" == "true" ]] || [[ "$APPROVE_GITIGNORE" == "true" ]]; then
  echo "ℹ Committing changes..."

  # Recompute generated_files and managed_paths from the approved plan, reading
  # file contents from the project tree (not staging) so hashes reflect the final state.
  GENERATED_FILES="[]"
  MANAGED_PATHS="[]"
  while IFS= read -r -d '' file; do
    [[ -f "$file" ]] || continue
    HASH=$(wf_sha256 "$file")
    GENERATED_FILES=$(jq --arg path "$file" --arg hash "$HASH" '. += [{"path": $path, "hash": $hash, "managed": true}]' <<< "$GENERATED_FILES")
    MANAGED_PATHS=$(jq --arg path "$file" '. += [$path]' <<< "$MANAGED_PATHS")
  done < <(jq -j '.added[]?, .updated[]?, .unchanged[]? | .path + "\u0000"' "$PLAN")

  # Write .wizard-managed-files.json with the complete set of managed files
  TARGET_VERSION=$(wf_fetch_version)
  generated_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  jq -n \
    --arg version "$TARGET_VERSION" \
    --arg generated_at "$generated_at" \
    --argjson files "$GENERATED_FILES" \
    '{wizard_version: $version, generated_at: $generated_at, files: $files}' > ".wizard-managed-files.json"

  # Update state build_plan
  jq --argjson files "$GENERATED_FILES" --argjson paths "$MANAGED_PATHS" \
     '.build_plan.generated_files = $files | .build_plan.managed_paths = $paths | .updated_at = (now | todate)' "$WF_STATE" > "$WF_STATE.tmp"
  mv "$WF_STATE.tmp" "$WF_STATE"

  # Add to .gitignore (ensure a trailing newline first and use an exact line match).
  _gi_add() {
    local line="$1"
    if ! grep -qxF "$line" .gitignore 2>/dev/null; then
      if [ -f .gitignore ] && [ "$(tail -c1 .gitignore | wc -l | tr -d '[:space:]')" -eq 0 ]; then
        echo >> .gitignore
      fi
      printf '%s\n' "$line" >> .gitignore
      GITIGNORE_MODIFIED=true
    fi
  }

  GITIGNORE_MODIFIED=false
  if [[ "$APPROVE_GITIGNORE" == "true" ]]; then
    _gi_add ".wizard-managed-files.json"
    _gi_add "!.agents/"

    while IFS= read -r ide; do
      case "$ide" in
        claude-code) _gi_add "!.claude/" ;;
        cursor) _gi_add "!.cursor/" ;;
        windsurf) _gi_add "!.windsurf/"; _gi_add "!.devin/" ;;
        kiro) _gi_add "!.kiro/" ;;
        codex) _gi_add "!.codex/" ;;
        gemini-cli)
          _gi_add "!.gemini/"
          _gi_add "!GEMINI.md"
          ;;
        antigravity) _gi_add "!ANTIGRAVITY.md" ;;
        opencode) _gi_add "!.opencode/" ;;
        vscode-copilot)
          _gi_add "!.github/copilot-instructions.md"
          _gi_add "!.github/prompts/"
          ;;
      esac
    done < <(jq -r '.answers.ides[]?' "$WF_STATE" 2>/dev/null)
  else
    echo "ℹ .gitignore changes not approved; skipping .gitignore mutation"
  fi

  # Reflect the .gitignore change in the refresh plan so it is approved/committed explicitly.
  if [ "$GITIGNORE_MODIFIED" = true ]; then
    if ! jq -e '.updated[]? | select(.path == ".gitignore")' "$PLAN" >/dev/null 2>&1; then
      GI_OLD_HASH=""
      if git rev-parse --verify HEAD >/dev/null 2>&1; then
        TMP_GI=$(mktemp)
        if git show HEAD:.gitignore > "$TMP_GI" 2>/dev/null; then
          GI_OLD_HASH=$(wf_sha256 "$TMP_GI")
        fi
        rm -f "$TMP_GI"
      fi
      GI_NEW_HASH=$(wf_sha256 .gitignore)
      jq --arg path ".gitignore" \
         --arg old_hash "$GI_OLD_HASH" \
         --arg new_hash "$GI_NEW_HASH" \
         '.updated += [{"path": $path, "old_hash": $old_hash, "new_hash": $new_hash}]' "$PLAN" > "$PLAN.tmp"
      mv "$PLAN.tmp" "$PLAN"
    fi
  fi

  # Stage only the paths the user explicitly approved (null-delimited to handle
  # spaces and avoid `git add -A` dragging in unrelated user changes). Do NOT
  # reset the whole index: `git reset --mixed HEAD` would unstage unrelated work
  # the user may have staged. The commit below uses an explicit pathspec, so it
  # contains ONLY the approved paths.
  GIT_ADD_LIST=$(mktemp)
  if [[ "$APPROVE_ADDED" == "true" ]]; then
    jq -j '.added[]?.path | select(. != ".git" and (startswith(".git/") | not)) + "\u0000"' "$PLAN" >> "$GIT_ADD_LIST"
  fi
  if [[ "$APPROVE_UPDATED" == "true" ]]; then
    jq -j '.updated[]?.path | select(. != ".git" and (startswith(".git/") | not)) + "\u0000"' "$PLAN" >> "$GIT_ADD_LIST"
  fi
  if [ "$GITIGNORE_MODIFIED" = true ]; then
    printf '.gitignore\0' >> "$GIT_ADD_LIST"
  fi
  if [ -s "$GIT_ADD_LIST" ]; then
    # Force-add: every path here was explicitly approved by the user, and some
    # (e.g. generated dotfiles) may be gitignored. Without -f, `git add` exits 1
    # under set -e and the trap aborts the refresh mid-flight, leaving copied
    # files in the working tree without a commit.
    git add -f --pathspec-from-file="$GIT_ADD_LIST" --pathspec-file-nul
  fi
  rm -f "$GIT_ADD_LIST"

  # Commit exactly the approved paths (working-tree content). Other pre-staged
  # user files stay in the index and are NOT included in this commit.
  COMMIT_PATHS=$(mktemp)
  if [[ "$APPROVE_ADDED" == "true" ]]; then
    jq -j '.added[]?.path | select(. != ".git" and (startswith(".git/") | not)) + "\u0000"' "$PLAN" >> "$COMMIT_PATHS"
  fi
  if [[ "$APPROVE_UPDATED" == "true" ]]; then
    jq -j '.updated[]?.path | select(. != ".git" and (startswith(".git/") | not)) + "\u0000"' "$PLAN" >> "$COMMIT_PATHS"
  fi
  if [[ "$APPROVE_DELETED" == "true" ]]; then
    jq -j '.deleted[]?.path | select(. != ".git" and (startswith(".git/") | not)) + "\u0000"' "$PLAN" >> "$COMMIT_PATHS"
  fi
  if [[ "$APPROVE_DELETED_MODIFIED" == "true" ]]; then
    jq -j '.deleted_modified[]?.path | select(. != ".git" and (startswith(".git/") | not)) + "\u0000"' "$PLAN" >> "$COMMIT_PATHS"
  fi
  if [ "$GITIGNORE_MODIFIED" = true ]; then
    printf '.gitignore\0' >> "$COMMIT_PATHS"
  fi

  if [ -s "$COMMIT_PATHS" ]; then
    COMMIT_MSG=$(cat <<EOF
chore: refresh workflow to v$TARGET_VERSION

- Updated AGENTS.md with new project info
- Added $(jq '.added | length' "$PLAN") new files
- Updated $(jq '.updated | length' "$PLAN") files
- Removed $(jq '.deleted | length' "$PLAN") deprecated files
- Removed $(jq '.deleted_modified | length' "$PLAN") modified-deprecated files

Generated with /wf-refresh
EOF
)

    # git diff does NOT support --pathspec-from-file (usage error 129); read the
    # approved paths into positional arguments so the guard is portable.
    COMMIT_PATH_ARGS=()
    while IFS= read -r -d '' p; do
      COMMIT_PATH_ARGS+=("$p")
    done < "$COMMIT_PATHS"

    if git diff --cached --quiet -- "${COMMIT_PATH_ARGS[@]}"; then
      echo "ℹ Approved paths have no staged changes; skipping commit"
    else
      git commit -m "$COMMIT_MSG" --pathspec-from-file="$COMMIT_PATHS" --pathspec-file-nul
    fi
  else
    echo "ℹ No approved paths to commit"
  fi
else
  echo "ℹ No changes approved; skipping commit (no files were written)"
fi

# Staging and plan are cleaned by the EXIT trap installed above.

echo "✓ Phase R6 complete"
echo "ℹ Next: git push (when ready)"
```

---

## End of /wf-refresh

After Phase R6, the refresh is complete. Verify with:

```bash
git log -1 -p
```
