# Refresh orchestrator — phases R-1 through R6

This file is read as instructions by the agent running `/wf-refresh`. **Do not `source` this Markdown file.** Execute each fenced bash block in order **under `bash`, never zsh** (the blocks use bash arrays and `$BASH_VERSION` guards), pausing for user approval at Phase R5.

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

# This library uses bash arrays and version comparison: refuse to run under
# zsh/sh, where ${ARRAY[0]} is empty (1-indexed arrays) and cat '' fails.
if [[ -z "${BASH_VERSION:-}" ]]; then
  echo "ERROR: refresh-lib.sh must run under bash (zsh/sh detected). Re-run /wf-refresh with bash." >&2
  exit 1
fi

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
# NEVER fall back to a hardcoded version: an unknown remote version must
# surface as empty so the caller can abort instead of silently continuing.
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
    # Strip a leading 'v' BEFORE the emptiness check: VERSION="v" alone would
    # otherwise pass the -z check and printf an empty string.
    version="${version#v}"
    printf '%s' "$version"
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

# Remove a prompt line from the FU5 pending manifest once it has been answered
# (via WF_REFRESH_ANSWERS, WF_REFRESH_DEFAULT_ANSWER, or cancel semantics).
# Without this, a resumed run consumes the answer but leaves the stale line
# behind in .wizard-pending-prompts, so a later collection sweep re-emits an
# already-answered question.
_wf_pending_remove() {
  local prompt="$1"
  local pending_file="${WF_DIR}/.wizard-pending-prompts"
  [ -f "$pending_file" ] || return 0
  local tmp="${pending_file}.tmp"
  # grep exits 1 when EVERY line matched (result is empty): tolerate it.
  grep -vFx -- "$prompt" "$pending_file" > "$tmp" || true
  mv "$tmp" "$pending_file"
}

# Ask a yes/no question safely in BOTH tty and non-tty (agent-driven) contexts.
# In an interactive tty it prompts like a normal read -n 1. When stdin is EOF or
# not a tty (agent run), a bare `read` would fail under `set -e` and abort the
# script. In that case, resolution order is:
#   1. WF_REFRESH_ANSWERS — per-question answers, "prompt=answer" pairs joined
#      by "|" (prompts never contain "|" or "="). The match is exact on the
#      prompt string.
#   2. WF_REFRESH_DEFAULT_ANSWER ("yes" or "no") — global fallback.
#   3. The "cancel" second argument: treat the empty/garbage reply as NO
#      (return 1) instead of aborting.
# If none of these applies in non-tty mode, record the pending prompt in a
# manifest file and return 3 (distinct from abort 2 and success 0/no 1).
# The R5 gate will collect ALL pending prompts and emit GENTLE_AI_WF_REFRESH_NEEDS.
# Optional second argument "cancel": in non-tty mode without a default answer,
# treat the empty/garbage reply as NO (return 1) instead of aborting.
_ask_yesno_safe() {
  local prompt="$1"
  local cancel_on_empty="${2:-}"
  local reply leftover
  if ! read -p "$prompt [y/n] " -n 1 -r reply 2>/dev/null; then
    reply=""
  fi
  echo
  if [[ ! -t 0 ]]; then
    # Drain the rest of the piped line so a leftover does not corrupt the next
    # question.
    read -r leftover 2>/dev/null || true
    reply="${reply//[$'\n\r']/}"
    if [[ "$reply" =~ ^[Yy]$ ]]; then
      return 0
    elif [[ "$reply" =~ ^[Nn]$ ]]; then
      return 1
    fi
    # Per-question answer first (exact prompt match), then the global default.
    local pq
    pq=$(_wf_answers_get "$prompt")
    if [ -n "$pq" ]; then
      _wf_pending_remove "$prompt"
      echo "(non-interactive — WF_REFRESH_ANSWERS[$prompt]=$pq)"
      if [[ "$pq" =~ ^[Yy](es)?$ ]]; then
        return 0
      elif [[ "$pq" =~ ^[Nn](o)?$ ]]; then
        return 1
      else
        echo "ERROR: WF_REFRESH_ANSWERS value for '$prompt' is '$pq'; expected yes/no." >&2
        exit 2
      fi
    fi
    # Non-tty with an empty/garbage reply (e.g. a leftover newline): use
    # WF_REFRESH_DEFAULT_ANSWER or record as pending instead of failing.
    if [ "${WF_REFRESH_DEFAULT_ANSWER:-}" = "yes" ]; then
      _wf_pending_remove "$prompt"
      echo "(non-interactive — using WF_REFRESH_DEFAULT_ANSWER=yes)"
      return 0
    elif [ "${WF_REFRESH_DEFAULT_ANSWER:-}" = "no" ]; then
      _wf_pending_remove "$prompt"
      echo "(non-interactive — using WF_REFRESH_DEFAULT_ANSWER=no)"
      return 1
    elif [ "$cancel_on_empty" = "cancel" ]; then
      _wf_pending_remove "$prompt"
      echo "(non-interactive — no WF_REFRESH_ANSWERS/WF_REFRESH_DEFAULT_ANSWER; treating as NO)"
      return 1
    else
      # FU5: Record pending prompt for manifest instead of aborting.
      local pending_file="${WF_DIR}/.wizard-pending-prompts"
      echo "$prompt" >> "$pending_file"
      echo "(non-interactive — prompt recorded for manifest: '$prompt')"
      return 3
    fi
  fi
  # TTY: any non-y/n reply is NO (interactive users can simply re-run).
  if [[ "$reply" =~ ^[Yy]$ ]]; then
    return 0
  else
    return 1
  fi
}

# Look up a per-question answer from WF_REFRESH_ANSWERS (format:
# "prompt=yes|prompt=no|..."). Exact prompt match; empty when absent.
_wf_answers_get() {
  local wanted="$1"
  local pair
  [ -n "${WF_REFRESH_ANSWERS:-}" ] || return 0
  IFS='|' read -r -a _wf_answers_pairs <<< "$WF_REFRESH_ANSWERS"
  for pair in "${_wf_answers_pairs[@]}"; do
    if [[ "$pair" == "$wanted="* ]]; then
      printf '%s' "${pair#*=}"
      return 0
    fi
  done
  printf ''
}

# Extract a "## <header>" section body from AGENTS.md (up to the next "## "
# header or a WF: DO NOT REGENERATE marker). Trims leading/trailing blank
# lines only; interior blank lines are preserved.
# Lives in refresh-lib.sh (not inline in R1): R1 calls it during discovery
# (Commands / Project Structure / Project MCPs) BEFORE the point where it
# used to be defined — bash runs top-down, so those calls failed with
# "command not found" and degraded exactly those AGENTS.md sections.
_wf_section() {
  awk -v h="$1" '
    $0 ~ "^## " h "$" { on=1; next }
    on && /^## / { exit }
    on && /^<!-- WF: DO NOT REGENERATE -->/ { exit }
    on { print }
  ' AGENTS.md | sed -e '/./,$!d' -e :a -e '/^\n*$/{$d;N;ba' -e '}'
}

# Fail-fast prompt gate for pre-R5 phases (R1/R2). In non-tty runs an
# unanswered prompt must STOP the phase immediately instead of continuing
# with default-"no" behavior: staging would be built from stale info and the
# answer collected later by the R5 manifest would have no consumer (the
# owning phase never re-runs under WF_REFRESH_RESUME=1). Mirrors the
# restart-semantics pattern R-1 uses for "Update global commands?".
# Writes .wizard-resume-phase so a resumed run re-enters THIS phase.
_require_answer_or_stop() {
  local prompt="$1" phase_id="$2"
  local rc=0
  _ask_yesno_safe "$prompt" || rc=$?
  case "$rc" in
    0|1) return "$rc" ;;
    3)
      printf '%s\n' "$phase_id" > "${WF_DIR}/.wizard-resume-phase"
      echo "GENTLE_AI_WF_REFRESH_NEEDS=prompt=${prompt}"
      echo "✗ Non-tty run requires an answer for '${prompt}' before ${phase_id} can continue." >&2
      echo "  Set WF_REFRESH_ANSWERS='${prompt}=yes' (or =no) and re-run with WF_REFRESH_RESUME=1." >&2
      exit 3
      ;;
    *)
      return "$rc"
      ;;
  esac
}

# Resume-marker gate for phases R-1..R4: skip this phase when a resumed run
# targets a later phase; consume the marker when this phase is the target.
# Without a marker (fresh run, or legacy resume-to-R5) this is a no-op, so
# the pre-existing WF_REFRESH_RESUME contract keeps working unchanged.
_wf_resume_gate() {
  local phase_id="$1"
  local marker="${WF_DIR}/.wizard-resume-phase"
  if [[ "${WF_REFRESH_RESUME:-}" = "1" && -f "$marker" ]]; then
    local marked
    marked=$(cat "$marker")
    if [[ "$marked" != "$phase_id" ]]; then
      echo "ℹ Skipping ${phase_id} (resume targets ${marked})"
      exit 0
    fi
    rm -f "$marker"
    echo "ℹ Resuming at ${phase_id} (WF_REFRESH_RESUME=1)"
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
    # Defensive: skip missing block files. Under zsh (1-indexed arrays)
    # BLOCK_FILES[0] is empty, which previously produced `cat: : No such file`.
    [[ -n "$BF" && -f "$BF" ]] || continue
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

# Reinsert the "Gentle AI — Legacy Path Bridge for Windsurf/Devin" rule into
# the IDE-specific rules files when Windsurf/Devin is an active IDE.
# The bridge belongs in .windsurf/rules/project.md and .devin/rules/project.md
# (not AGENTS.md), because it's IDE-specific configuration for legacy path resolution.
# $1 (optional) is the staging directory — defaults to .wizard-staging.
# Idempotent: skips when the rule is already present.
reinsert_legacy_bridge() {
  local STAGING_DIR IDES RULE_FILE
  STAGING_DIR="${1:-.wizard-staging}"
  IDES=$(jq -r '.answers.ides[]?' "$WF_STATE" 2>/dev/null)
  if ! echo "$IDES" | grep -q "windsurf"; then
    return 0
  fi
  RULE_FILE="${WF_DIR}/temp-files/AGENTS.md"
  if [ ! -f "$RULE_FILE" ]; then
    return 0
  fi

  # Target files: both Windsurf and Devin rules
  for TARGET in "$STAGING_DIR/.windsurf/rules/project.md" "$STAGING_DIR/.devin/rules/project.md"; do
    if [ ! -f "$TARGET" ]; then
      # Create directory and file if missing (satellite may not exist yet)
      mkdir -p "$(dirname "$TARGET")"
      printf '# Project Rules\n\n' > "$TARGET"
    fi
    if grep -q "Gentle AI — Legacy Path Bridge" "$TARGET"; then
      echo "  ℹ Legacy path bridge already present in $TARGET"
      continue
    fi
    # Find first heading or use line 1
    TITLE_LINE=$(grep -n '^# ' "$TARGET" | head -1 | cut -d: -f1)
    if [ -z "$TITLE_LINE" ]; then
      TITLE_LINE=1
    fi
    {
      head -n "$TITLE_LINE" "$TARGET"
      cat "$RULE_FILE"
      tail -n +$((TITLE_LINE + 1)) "$TARGET"
    } > "$TARGET.tmp"
    mv "$TARGET.tmp" "$TARGET"
    if grep -q "Gentle AI — Legacy Path Bridge" "$TARGET"; then
      echo "  ✓ Windsurf/Devin legacy path bridge inserted into $TARGET"
    else
      echo "  ⚠ Legacy path bridge MISSING from $TARGET after insert." >&2
    fi
  done
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

# Resume-marker gate: if a resumed run targets a later phase, skip R-1.
# No marker (fresh run or legacy resume-to-R5) -> no-op.
_wf_resume_gate "R-1"

# FU5: Handle WF_REFRESH_RESUME=1 — skip prompt if answer provided via WF_REFRESH_ANSWERS
# The prompt "Update global commands?" is matched exactly in _wf_answers_get.
if [[ "${WF_REFRESH_RESUME:-}" = "1" ]]; then
  RESUME_ANSWER=$(_wf_answers_get "Update global commands?")
  if [[ -n "$RESUME_ANSWER" ]]; then
    echo "ℹ Resuming Phase R-1 with WF_REFRESH_ANSWERS[Update global commands?]=$RESUME_ANSWER"
    LOCAL_VERSION=""
    UNIVERSAL_SKILL="$HOME/.agents/skills/wf-refresh/SKILL.md"
    if [[ -f "$UNIVERSAL_SKILL" ]]; then
      LOCAL_VERSION=$(sed -n 's/^version: *\([^ ]*\).*/\1/p' "$UNIVERSAL_SKILL" | head -1)
    fi
    if [[ -z "$LOCAL_VERSION" ]]; then
      LOCAL_VERSION=$(jq -r '.wizard_version // empty' "$WF_STATE" 2>/dev/null || true)
    fi
    LOCAL_VERSION="${LOCAL_VERSION:-0.7.1-beta.1}"
    LOCAL_VERSION="${LOCAL_VERSION#v}"

    REMOTE_VERSION=$(curl -fsSL "${WF_RAW}/VERSION" 2>/dev/null | head -1 || true)
    REMOTE_VERSION="${REMOTE_VERSION:-$(wf_fetch_version)}"
    REMOTE_VERSION="${REMOTE_VERSION#v}"

    if [[ -z "$REMOTE_VERSION" ]]; then
      echo "✗ Could not fetch the remote wizard version (network issue?)." >&2
      echo "  Refusing to continue with a stale or hardcoded version." >&2
      echo "  Re-run /wf-refresh when the network is available. No changes were made." >&2
      exit 1
    fi

    if [[ "$LOCAL_VERSION" == "$REMOTE_VERSION" ]]; then
      echo "✓ Wizard is up-to-date"
      exit 0
    fi

    if version_lt "$LOCAL_VERSION" "$REMOTE_VERSION"; then
      if [[ "$RESUME_ANSWER" =~ ^[Yy](es)?$ ]]; then
        echo "⚠ Wizard is outdated (local: $LOCAL_VERSION, remote: $REMOTE_VERSION)"
        echo "ℹ Running install.sh (from WF_REFRESH_ANSWERS=yes)..."
        INSTALL_SH="${WF_DIR}/install.sh"
        if curl -fsSL "${WF_RAW}/install.sh" -o "$INSTALL_SH" 2>/dev/null && [[ -s "$INSTALL_SH" ]]; then
          if bash "$INSTALL_SH"; then
            echo "⚠ Global commands updated to $REMOTE_VERSION."
            echo "  Open a NEW session and re-run /wf-refresh so the updated wizard drives the refresh."
            # Exit 3 (not 0): the orchestrator must stop here. Continuing would
            # run R0-R4 with the stale wizard code downloaded at session start.
            exit 3
          else
            echo "⚠ install.sh failed; continuing anyway"
          fi
        else
          echo "⚠ Could not download install.sh from ${WF_RAW}/install.sh; skipping update"
        fi
      else
        echo "ℹ Skipping global commands update (from WF_REFRESH_ANSWERS=no)"
      fi
    else
      echo "⚠ Local version is ahead of remote (local: $LOCAL_VERSION, remote: $REMOTE_VERSION)"
    fi
    echo "✓ Phase R-1 complete (resumed)"
    exit 0
  fi
  # No answer provided for this prompt, continue to normal interactive/non-interactive logic
fi

# FU5: Clear pending prompts file at start of fresh run (R-1 is first phase).
# Also clear any stale resume-phase marker from a previous interrupted run.
rm -f "${WF_DIR}/.wizard-pending-prompts" "${WF_DIR}/.wizard-resume-phase"

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
  echo "✗ Could not fetch the remote wizard version (network issue?)." >&2
  echo "  Refusing to continue with a stale or hardcoded version." >&2
  echo "  Re-run /wf-refresh when the network is available. No changes were made." >&2
  exit 1
fi

echo "ℹ Remote wizard version: $REMOTE_VERSION"

if [[ "$LOCAL_VERSION" == "$REMOTE_VERSION" ]]; then
  echo "✓ Wizard is up-to-date"
  exit 0
fi

if version_lt "$LOCAL_VERSION" "$REMOTE_VERSION"; then
  echo "⚠ Wizard is outdated (local: $LOCAL_VERSION, remote: $REMOTE_VERSION)"
  UPDATE_RC=0
  _ask_yesno_safe "Update global commands?" || UPDATE_RC=$?
  if [[ "$UPDATE_RC" = "3" ]]; then
    # Restart-semantics prompt: this answer decides whether the wizard itself is
    # replaced, so it must be resolved BEFORE any refresh work. Cut the pipeline
    # here instead of deferring to R5 — R0-R4 work would be wasted once the user
    # answers "yes" (install.sh requires a fresh session anyway).
    rm -f "${WF_DIR}/.wizard-pending-prompts"
    echo "GENTLE_AI_WF_REFRESH_NEEDS=prompt=Update global commands?"
    echo "✗ Non-tty run requires an answer for 'Update global commands?' before any refresh work." >&2
    echo "  Set WF_REFRESH_ANSWERS='Update global commands?=yes' (or =no) and re-run with WF_REFRESH_RESUME=1." >&2
    exit 3
  elif [[ "$UPDATE_RC" = "0" ]]; then
    # install.sh lives in the wizard repo, not in the project directory.
    INSTALL_SH="${WF_DIR}/install.sh"
    if curl -fsSL "${WF_RAW}/install.sh" -o "$INSTALL_SH" 2>/dev/null && [[ -s "$INSTALL_SH" ]]; then
      echo "ℹ Running install.sh..."
      if bash "$INSTALL_SH"; then
        # The global commands just changed: continuing in this session would mix
        # the old and new wizard versions. Stop and ask for a fresh session.
        # Exit 3 (not 0) so the orchestrator's `|| exit` stops the run instead of
        # proceeding to R0 with stale wizard code.
        echo "⚠ Global commands updated to $REMOTE_VERSION."
        echo "  Open a NEW session and re-run /wf-refresh so the updated wizard drives the refresh."
        exit 3
      else
        echo "⚠ install.sh failed; continuing anyway"
      fi
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

# Resume-marker gate: skip R0 when a resumed run targets a later phase.
_wf_resume_gate "R0"

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

# Copy state to staging for atomic refresh operations (R2-R6 operate on staging)
STAGING_DIR=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")
mkdir -p "$STAGING_DIR"
STAGING_STATE="$STAGING_DIR/wizard-state.json"
cp "$WF_STATE" "$STAGING_STATE"
echo "✓ State copied to staging: $STAGING_STATE"

# Read IDEs from state (user's original selection), do NOT auto-detect from directories
# Auto-detection would add IDEs the user never selected (e.g., .claude/ from old runs)
IDES=$(jq -r '.answers.ides[]?' "$WF_STATE" 2>/dev/null)

if [[ -z "$IDES" ]]; then
  echo "⚠ No active IDEs in state"
  IDES_JSON='[]'
else
  echo "ℹ Active IDEs from state: $IDES"
  IDES_JSON=$(printf '%s\n' $IDES | jq -R . | jq -s .)
fi
# Keep answers.ides as-is (user's choice). Do not merge detected directories.

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

# Resume-marker gate: skip R1 when a resumed run targets a later phase;
# when R1 is the target, consume the marker and run with WF_REFRESH_ANSWERS.
_wf_resume_gate "R1"

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
OLD_COMMANDS=$(jq -r '.discovery.commands // ""' "$WF_STATE")

# Always re-detect the full script list from package.json on every refresh.
# FU2: The old behavior only detected when state lacked commands; now we always
# re-detect so stale partial lists are replaced by the fresh full list.
# OLD_COMMANDS is fallback only when package.json is missing or jq fails.
COMMANDS=""
if [[ -f package.json ]] && command -v jq >/dev/null 2>&1; then
  COMMANDS=$(jq -r '[.scripts | keys[] | "npm run " + .] | join(", ")' package.json 2>/dev/null || true)
fi
if [[ -z "$COMMANDS" ]]; then
  COMMANDS="$OLD_COMMANDS"
fi

# FU3a: Parse AGENTS.md Commands section into name->description map and emit merged bullets.
# The builder renders discovery.commands verbatim, so we write the bulleted list to state.
# This runs unconditionally when package.json exists and we have script names.
if [[ -f package.json ]] && command -v jq >/dev/null 2>&1; then
  # Extract fresh script names from package.json (without "npm run " prefix for matching)
  SCRIPT_NAMES=$(jq -r '.scripts | keys[]' package.json 2>/dev/null || true)
  
  # Parse current AGENTS.md Commands section for descriptions (if AGENTS.md exists).
  # Parallel indexed arrays instead of `declare -A`: associative arrays need
  # bash 4+, but stock macOS still ships bash 3.2.
  CMD_NAMES=()
  CMD_DESCS=()
  if [[ -f AGENTS.md ]]; then
    # Use awk to extract the Commands section and parse bullets/lines
    # Formats supported:
    #   - `npm run <name>` — <description>   (backticked rich format)
    #   - npm run <name> — <description>
    #   - npm run <name> - <description>
    #   - npm run <name>  (no description)
    #   <name> — <description>
    while IFS= read -r line; do
      # Strip backticks FIRST: the documented rich format is
      # "- `npm run dev` — Start development server" and the name class below
      # would otherwise capture "`npm" (backtick is not whitespace) and never
      # match the script name, silently dropping every description.
      line="${line//\`/}"
      # Name class allows ':' (canonical npm scripts like test:e2e /
      # test:coverage) and stops at whitespace or the em-dash/hyphen separator.
      if [[ "$line" =~ ^[[:space:]]*[-*]?[[:space:]]*(npm[[:space:]]+run[[:space:]]+)?([^[:space:]—-]+)[[:space:]]*[—-][[:space:]]*(.+)$ ]]; then
        CMD_NAMES+=("${BASH_REMATCH[2]}")
        CMD_DESCS+=("${BASH_REMATCH[3]}")
      elif [[ "$line" =~ ^[[:space:]]*[-*]?[[:space:]]*(npm[[:space:]]+run[[:space:]]+)?([^[:space:]—-]+)[[:space:]]*$ ]]; then
        CMD_NAMES+=("${BASH_REMATCH[2]}")
        CMD_DESCS+=("")
      fi
    done < <(_wf_section "Commands")
  fi
  
  # Emit merged bullets: - `npm run <name>` — <description> (description
  # omitted when unknown). Backticked shape matches the documented rich format
  # so the next refresh round-trips through the parser unchanged.
  # Last match wins so later duplicates override earlier ones.
  MERGED_COMMANDS=""
  MERGED_DESC_COUNT=0
  SCRIPT_TOTAL=0
  while IFS= read -r script; do
    [[ -z "$script" ]] && continue
    SCRIPT_TOTAL=$((SCRIPT_TOTAL+1))
    desc=""
    for _ci in "${!CMD_NAMES[@]}"; do
      if [[ "${CMD_NAMES[_ci]}" = "$script" ]]; then
        desc="${CMD_DESCS[_ci]}"
      fi
    done
    if [[ -n "$desc" ]]; then
      MERGED_COMMANDS+="- \`npm run $script\` — $desc"$'\n'
      MERGED_DESC_COUNT=$((MERGED_DESC_COUNT+1))
    else
      MERGED_COMMANDS+="- \`npm run $script\`"$'\n'
    fi
  done <<< "$SCRIPT_NAMES"
  
  # Remove trailing newline
  MERGED_COMMANDS="${MERGED_COMMANDS%$'\n'}"
  
  if [[ -n "$MERGED_COMMANDS" ]]; then
    COMMANDS="$MERGED_COMMANDS"
    # Write merged commands (with descriptions) to staging state so Builder uses them
    STAGING_DIR=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")
    STAGING_STATE_BF="$STAGING_DIR/wizard-state.json"
    WF_STATE="$STAGING_STATE_BF" _apply_jq_filter --arg commands "$MERGED_COMMANDS" '.discovery.commands = $commands'
    echo "✓ Merged $MERGED_DESC_COUNT/$SCRIPT_TOTAL command descriptions from AGENTS.md (staging)"
    if [[ "$MERGED_DESC_COUNT" -eq 0 ]]; then
      echo "⚠ No command descriptions matched the current AGENTS.md Commands section — re-run /wf-init phase1 if this section should be annotated"
    fi
  fi
fi

# FU3c: Regenerate Project Structure from live tree and merge comments from AGENTS.md
# Deterministic find: depth 2. Exclude build/output/dependency directories BOTH
# themselves and their children ("-not -path X" alone misses the directory when
# the pattern requires a trailing slash component).
LIVE_STRUCTURE=$(find . -mindepth 1 -maxdepth 2 -type d \
  -not -path "./node_modules" -not -path "./node_modules/*" \
  -not -path "./.git" -not -path "./.git/*" \
  -not -path "./dist" -not -path "./dist/*" \
  -not -path "./build" -not -path "./build/*" \
  -not -path "./coverage" -not -path "./coverage/*" \
  -not -path "./playwright-report" -not -path "./playwright-report/*" \
  -not -path "./test-results" -not -path "./test-results/*" \
  -not -path "./.wizard-*" \
  2>/dev/null | sed 's|^\./||' | sort)

if [[ -n "$LIVE_STRUCTURE" ]]; then
  # Parse old AGENTS.md Project Structure for comments (path -> comment).
  # Parallel indexed arrays instead of `declare -A` (bash 3.2 compatible).
  # Paths are stored WITHOUT trailing slash so they match the live tree's
  # `find` output exactly ("src/" in prose vs "src" from find never matched,
  # which silently dropped every merged comment); the trailing slash is
  # re-added on emission to keep the documented "dir/ — comment" shape.
  STRUCT_PATHS=()
  STRUCT_COMMENTS=()
  if [[ -f AGENTS.md ]]; then
    # Extract lines like "src/ — single source of truth" or "templates/  # single source of truth"
    while IFS= read -r line; do
      # Normalize tree-drawing glyphs FIRST ("├── src/" -> "src/"): box-drawing
      # chars are not [[:space:]], so without this the path class never reached
      # them and every comment in a tree-formatted section was silently dropped.
      line="${line//[│├└─]/}"
      line="${line#"${line%%[![:space:]]*}"}"   # ltrim
      # Match patterns: "path/ — comment" or "path/  # comment" or "path/ -- comment".
      # The separator class is [—#-] (dash LAST): "[—-#]" would form the range
      # em-dash..'#', which is empty, so em-dash comments never matched.
      if [[ "$line" =~ ^[-*]?[[:space:]]*([^[:space:]:#—-]+/)[[:space:]]*[—#-][[:space:]]*(.+)$ ]]; then
        STRUCT_PATHS+=("${BASH_REMATCH[1]%/}")
        STRUCT_COMMENTS+=("${BASH_REMATCH[2]}")
      elif [[ "$line" =~ ^[-*]?[[:space:]]*([^[:space:]:#—-]+/)[[:space:]]*$ ]]; then
        STRUCT_PATHS+=("${BASH_REMATCH[1]%/}")
        STRUCT_COMMENTS+=("")
      fi
    done < <(_wf_section "Project Structure")
  fi
  
  _struct_in_live() {
    # Membership test against the live tree list (exact line match).
    printf '%s\n' "$LIVE_STRUCTURE" | grep -Fxq "$1"
  }
  
  # Merge pass 1: surviving original entries first, in original order, with
  # their comments; drop paths that no longer exist on disk.
  MERGED_STRUCTURE=""
  for _si in "${!STRUCT_PATHS[@]}"; do
    _sp="${STRUCT_PATHS[_si]}"
    if _struct_in_live "$_sp"; then
      _sc="${STRUCT_COMMENTS[_si]}"
      if [[ -n "$_sc" ]]; then
        MERGED_STRUCTURE+="$_sp/ — $_sc"$'\n'
      else
        MERGED_STRUCTURE+="$_sp/"$'\n'
      fi
    fi
  done
  
  # Merge pass 2: newly detected directories (no original entry), sorted order.
  while IFS= read -r _lp; do
    [[ -z "$_lp" ]] && continue
    _known=0
    for _si in "${!STRUCT_PATHS[@]}"; do
      if [[ "${STRUCT_PATHS[_si]}" = "$_lp" ]]; then
        _known=1
        break
      fi
    done
    if [[ "$_known" = "0" ]]; then
      MERGED_STRUCTURE+="$_lp/"$'\n'
    fi
  done <<< "$LIVE_STRUCTURE"
  
  MERGED_STRUCTURE="${MERGED_STRUCTURE%$'\n'}"
  
  if [[ -n "$MERGED_STRUCTURE" ]]; then
    STAGING_DIR=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")
    STAGING_STATE_BF="$STAGING_DIR/wizard-state.json"
    # Downgrade guard: never trade a MORE informative section for a LESS
    # informative one. A fenced/tree-formatted original (written by /wf-init
    # discovery: hierarchy, files, comments) outranks the deterministic flat
    # regeneration (dirs only, depth 2) — keep it verbatim. Same guard when
    # regeneration would drop every inline comment the original had.
    OLD_ANNOTATED=0
    for _sc in "${STRUCT_COMMENTS[@]}"; do
      if [[ -n "$_sc" ]]; then OLD_ANNOTATED=$((OLD_ANNOTATED+1)); fi
    done
    NEW_ANNOTATED=$(printf '%s' "$MERGED_STRUCTURE" | grep -c ' — ' || true)
    RAW_STRUCTURE_SECTION=""
    if [[ -f AGENTS.md ]]; then
      RAW_STRUCTURE_SECTION=$(_wf_section "Project Structure")
    fi
    case "$RAW_STRUCTURE_SECTION" in
      *'```'*|*'│'*|*'├'*|*'└'*)
        WF_STATE="$STAGING_STATE_BF" _apply_jq_filter --arg st "$RAW_STRUCTURE_SECTION" '.discovery.conventions.structure = $st'
        echo "✓ Kept rich Project Structure section verbatim (tree/fenced format outranks flat regeneration)"
        ;;
      *)
        if [[ "$OLD_ANNOTATED" -gt 0 && "$NEW_ANNOTATED" -eq 0 ]]; then
          WF_STATE="$STAGING_STATE_BF" _apply_jq_filter --arg st "$RAW_STRUCTURE_SECTION" '.discovery.conventions.structure = $st'
          echo "⚠ Regenerated structure lost all $OLD_ANNOTATED inline comments — kept original section verbatim"
        else
          WF_STATE="$STAGING_STATE_BF" _apply_jq_filter --arg st "$MERGED_STRUCTURE" '.discovery.conventions.structure = $st'
          echo "✓ Regenerated structure from live tree ($NEW_ANNOTATED inline comments preserved)"
        fi
        ;;
    esac
  fi
fi

# FU3d: Re-detect MCPs from config files and merge purpose/setup from AGENTS.md
# Known MCP config locations
MCP_CONFIGS=(".mcp.json" ".cursor/mcp.json" ".windsurf/mcp.json")
DETECTED_MCPS=()
for mcp_config in "${MCP_CONFIGS[@]}"; do
  if [[ -f "$mcp_config" ]] && command -v jq >/dev/null 2>&1; then
    # Extract MCP names from config (assuming format like { "mcpServers": { "name": {...} } })
    names=$(jq -r '.mcpServers | keys[]?' "$mcp_config" 2>/dev/null || true)
    if [[ -n "$names" ]]; then
      while IFS= read -r name; do
        [[ -n "$name" ]] && DETECTED_MCPS+=("$name")
      done <<< "$names"
    fi
  fi
done
# Also check .github/copilot-instructions.md for MCP hints
if [[ -f ".github/copilot-instructions.md" ]]; then
  # Extract MCP names mentioned in the file (simple grep for known MCP names)
  known_mcps=("engrag" "context7" "playwright" "github" "supabase" "postgres" "stripe" "octokit")
  for known in "${known_mcps[@]}"; do
    if grep -qi "$known" ".github/copilot-instructions.md" 2>/dev/null; then
      DETECTED_MCPS+=("$known")
    fi
  done
fi
# Deduplicate
if [[ ${#DETECTED_MCPS[@]} -gt 0 ]]; then
  IFS=$'\n' DETECTED_MCPS=($(sort -u <<< "${DETECTED_MCPS[*]}"))
fi

# Parse old AGENTS.md MCP table for purpose/setup (3-col: | MCP | Purpose | Required setup |)
# Parallel indexed arrays instead of `declare -A`: associative arrays need
# bash 4+, but stock macOS still ships bash 3.2. Last match wins.
MCP_NAMES=()
MCP_PURPOSES=()
MCP_SETUPS=()
if [[ -f AGENTS.md ]]; then
  while IFS= read -r line; do
    # Match 3-col table rows: | name | purpose | setup |
    if [[ "$line" =~ ^\|[[:space:]]*([^|]+)[[:space:]]*\|[[:space:]]*([^|]+)[[:space:]]*\|[[:space:]]*([^|]+)[[:space:]]*\|$ ]]; then
      name="${BASH_REMATCH[1]}"
      purpose="${BASH_REMATCH[2]}"
      setup="${BASH_REMATCH[3]}"
      # Trim whitespace
      name=$(echo "$name" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      purpose=$(echo "$purpose" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      setup=$(echo "$setup" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      # Skip header and separator rows
      if [[ "$name" != "MCP" && "$name" != "---" && "$name" != "" ]]; then
        MCP_NAMES+=("$name")
        MCP_PURPOSES+=("$purpose")
        MCP_SETUPS+=("$setup")
      fi
    fi
  done < <(_wf_section "Project MCPs")
fi

# Build merged mcps array with purpose/setup
if [[ ${#DETECTED_MCPS[@]} -gt 0 ]]; then
  MCP_JSON=""
  for name in "${DETECTED_MCPS[@]}"; do
    purpose=""
    setup=""
    for _mi in "${!MCP_NAMES[@]}"; do
      if [[ "${MCP_NAMES[_mi]}" = "$name" ]]; then
        purpose="${MCP_PURPOSES[_mi]}"
        setup="${MCP_SETUPS[_mi]}"
      fi
    done
    if [[ -n "$purpose" || -n "$setup" ]]; then
      # Escape JSON strings
      p_escaped=$(printf '%s' "$purpose" | jq -Rs .)
      s_escaped=$(printf '%s' "$setup" | jq -Rs .)
      MCP_JSON+="{\"name\": \"$name\", \"active\": true, \"purpose\": $p_escaped, \"setup\": $s_escaped},"
    else
      MCP_JSON+="{\"name\": \"$name\", \"active\": true},"
    fi
  done
  MCP_JSON="[${MCP_JSON%,}]"
  
  if echo "$MCP_JSON" | jq -e 'type == "array"' >/dev/null 2>&1; then
    STAGING_DIR=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")
    STAGING_STATE_BF="$STAGING_DIR/wizard-state.json"
    WF_STATE="$STAGING_STATE_BF" _apply_jq_filter --argjson mcps "$MCP_JSON" '.mcps = $mcps'
    echo "✓ Re-detected MCPs from configs with merged purpose/setup"
  fi
fi

if [[ "$OLD_STACK" != "$STACK_KEY" ]] || [[ "$OLD_NODE" != "$NODE_ENGINE" ]] || [[ "$OLD_NPM" != "$NPM_MAJOR" ]] || [[ "$OLD_COMMANDS" != "$COMMANDS" ]]; then
  echo "⚠ Project content drift detected:"
  [[ "$OLD_STACK" != "$STACK_KEY" ]] && echo "  - Stack: $OLD_STACK → $STACK_KEY"
  [[ "$OLD_NODE" != "$NODE_ENGINE" ]] && echo "  - Node engine: $OLD_NODE → $NODE_ENGINE"
  [[ "$OLD_NPM" != "$NPM_MAJOR" ]] && echo "  - npm major: $OLD_NPM → $NPM_MAJOR"
  [[ "$OLD_COMMANDS" != "$COMMANDS" ]] && echo "  - Commands: $OLD_COMMANDS → $COMMANDS"

  # Fail-fast: in non-tty runs an unanswered prompt stops R1 here (before any
  # staging work) instead of silently taking the "no" path with stale info.
  if _require_answer_or_stop "Use updated project info?" "R1"; then
    # Write the drift to the STAGING state, not root: R6 promotes staging to
    # root at the end, so a root-only write would be silently clobbered.
    # Only write non-empty node_engine/npm_major to avoid clobbering good values with empty discovery results.
    STAGING_DIR=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")
    JQ_FILTER='.discovery.stack.stack_key = $stack_key | .discovery.git_commits = $git_commits | .discovery.commands = $commands'
    if [[ -n "$NODE_ENGINE" ]]; then
      JQ_FILTER="$JQ_FILTER | .discovery.node_engine = \$node_engine"
    fi
    if [[ -n "$NPM_MAJOR" ]]; then
      JQ_FILTER="$JQ_FILTER | .discovery.npm_major = \$npm_major"
    fi
    WF_STATE="$STAGING_DIR/wizard-state.json" _apply_jq_filter \
      --arg stack_key "$STACK_KEY" \
      --arg node_engine "$NODE_ENGINE" \
      --arg npm_major "$NPM_MAJOR" \
      --argjson git_commits "$GIT_COMMITS" \
      --arg commands "$COMMANDS" \
      "$JQ_FILTER"
    echo "✓ Updated discovery fields (staging)"
  else
    echo "ℹ Keeping existing discovery fields"
  fi
else
  echo "✓ No project drift detected"
fi

# --- Backfill richer AGENTS.md sections into staging state (Fix L) ---
# The builder renders flat state fields to generic fallbacks ("npm run build",
# "camelCase", "flat", "None configured"). When the current AGENTS.md already
# carries richer sections for those fields, preserve them into the staging
# state so a refresh does not flatten the project's own documentation.
STAGING_DIR=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")
STAGING_STATE_BF="$STAGING_DIR/wizard-state.json"

if [[ -f AGENTS.md ]]; then
  # _wf_section() lives in refresh-lib.sh. It is ALSO called earlier in this
  # phase (Commands / Project Structure / Project MCPs discovery); defining
  # it here was too late — bash executes top-down, so those calls failed.

  # 1. discovery.commands (fallback "npm run build")
  if [[ -z "$(jq -r '.discovery.commands // ""' "$STAGING_STATE_BF" 2>/dev/null)" ]]; then
    CUR=$(_wf_section "Commands")
    if [[ -n "$CUR" && "$CUR" != *"npm run build"* ]]; then
      WF_STATE="$STAGING_STATE_BF" _apply_jq_filter --arg commands "$CUR" '.discovery.commands = $commands'
      echo "✓ Backfilled discovery.commands from AGENTS.md"
    fi
  fi

  # 2. conventions.code_style (fallback "camelCase")
  if [[ -z "$(jq -r '.discovery.conventions.code_style // ""' "$STAGING_STATE_BF" 2>/dev/null)" ]]; then
    CUR=$(_wf_section "Code Style & Conventions")
    if [[ -n "$CUR" && "$CUR" != "camelCase" ]]; then
      WF_STATE="$STAGING_STATE_BF" _apply_jq_filter --arg cs "$CUR" '.discovery.conventions.code_style = $cs'
      echo "✓ Backfilled discovery.conventions.code_style from AGENTS.md"
    fi
  fi

  # 3. conventions.structure (fallback "flat")
  if [[ -z "$(jq -r '.discovery.conventions.structure // ""' "$STAGING_STATE_BF" 2>/dev/null)" ]]; then
    CUR=$(_wf_section "Project Structure")
    if [[ -n "$CUR" && "$CUR" != "flat" ]]; then
      WF_STATE="$STAGING_STATE_BF" _apply_jq_filter --arg st "$CUR" '.discovery.conventions.structure = $st'
      echo "✓ Backfilled discovery.conventions.structure from AGENTS.md"
    fi
  fi

  # 4. mcps: parse the markdown table into [{name, active}]
  if [[ "$(jq -c '.mcps // []' "$STAGING_STATE_BF" 2>/dev/null)" == "[]" ]]; then
    MCP_JSON=$(_wf_section "Project MCPs" | awk -F'|' '
      /^\| *[A-Za-z]/ && !/^ *\| *MCP *\|/ && !/^ *\| *[-: ]*\|/ {
        name=$2; active=$3; gsub(/^ +| +$/, "", name); gsub(/^ +| +$/, "", active)
        if (name != "") {
          a = (tolower(active) == "no" || active == "") ? "false" : "true"
          printf "{\"name\": \"%s\", \"active\": %s},", name, a
        }
      }')
    if [[ -n "$MCP_JSON" ]]; then
      MCP_JSON="[${MCP_JSON%,}]"
      if echo "$MCP_JSON" | jq -e 'type == "array"' >/dev/null 2>&1; then
        WF_STATE="$STAGING_STATE_BF" _apply_jq_filter --argjson mcps "$MCP_JSON" '.mcps = $mcps'
        echo "✓ Backfilled mcps from AGENTS.md table"
      fi
    fi
  fi
fi

echo "✓ Phase R1 complete"
```

---

## Phase R2: State/schema migration

Migrate `.wizard-state.json` from its current version to the actual `TARGET_VERSION` using cumulative, semver-aware migrations. **Operates on staging copy** (`$STAGING_STATE`).

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

# Resume-marker gate: skip R2 when a resumed run targets a later phase;
# when R2 is the target, consume the marker and run with WF_REFRESH_ANSWERS.
_wf_resume_gate "R2"

STAGING_STATE=".wizard-staging/wizard-state.json"

echo "ℹ Checking for state migrations..."

CURRENT_VERSION=$(jq -r '.wizard_version // "0.0.0"' "$STAGING_STATE")
CURRENT_VERSION="${CURRENT_VERSION#v}"

TARGET_VERSION=$(wf_fetch_version)
TARGET_VERSION="${TARGET_VERSION#v}"

echo "ℹ Current state version: $CURRENT_VERSION"
echo "ℹ Target version: $TARGET_VERSION"

# Use migrate_state function but target the staging state
WF_STATE="$STAGING_STATE" migrate_state "$CURRENT_VERSION" "$TARGET_VERSION"

# Unconditional legacy normalization (idempotent; runs even when versions match):
# 1. testing.layers may be a dict of active flags in legacy states -> array.
# 2. discovery.stack_key flat legacy -> nested discovery.stack.stack_key.
# The builder (R3) already tolerates both shapes; this keeps the state canonical.
WF_STATE="$STAGING_STATE" _apply_jq_filter '
  if (.testing.layers | type) == "object" then
    .testing.layers = [.testing.layers | to_entries[] | select(.value) | .key]
  else . end |
  .discovery.stack //= {} |
  .discovery.stack.stack_key = (.discovery.stack.stack_key // .discovery.stack_key) |
  del(.discovery.stack_key)
'

# R2 normalization (FU9): normalize corrupted node_engine/npm_major values.
# Values of "None" or "" become null so the builder defaults ("22"/"10") apply.
# Runs unconditionally and idempotently on every refresh.
WF_STATE="$STAGING_STATE" _apply_jq_filter '
  if .discovery.node_engine == "None" or .discovery.node_engine == "" then
    .discovery.node_engine = null
  else . end |
  if .discovery.npm_major == "None" or .discovery.npm_major == "" then
    .discovery.npm_major = null
  else . end
'

# Ask about new optional protocol features that are not present in the local
# state yet (features added by newer wizard versions). ci/cd/release_please are
# NOT asked here: they require the full phase47-cicd questionnaire and are
# configured via /wf-settings or /wf-init. Disabled features are recorded
# explicitly so they are never re-asked.
for FEATURE in decision_ladder tdd_protocol routing_abc; do
  if ! jq -e ".features.$FEATURE != null" "$STAGING_STATE" >/dev/null 2>&1; then
    echo "New optional feature available: $FEATURE"
    # Fail-fast: an unanswered feature prompt stops R2 immediately so the
    # answer is consumed by a re-run of THIS phase, not lost after R5.
    if _require_answer_or_stop "Enable $FEATURE?" "R2"; then
      WF_STATE="$STAGING_STATE" jq ".features.$FEATURE = true | .updated_at = (now | todate)" "$STAGING_STATE" > "$STAGING_STATE.tmp" && mv "$STAGING_STATE.tmp" "$STAGING_STATE"
      echo "✓ $FEATURE enabled"
    else
      WF_STATE="$STAGING_STATE" jq ".features.$FEATURE = false | .updated_at = (now | todate)" "$STAGING_STATE" > "$STAGING_STATE.tmp" && mv "$STAGING_STATE.tmp" "$STAGING_STATE"
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

# Resume-marker gate: skip R3 when a resumed run targets a later phase.
_wf_resume_gate "R3"

STAGING=".wizard-staging"
STAGING_STATE="$STAGING/wizard-state.json"
BASELINE=".wizard-refresh-baseline.json"

# Step 0: snapshot pre-Builder managed_paths/generated_files. R4's deletion
# diff depends on this baseline, so it must be captured BEFORE the Builder runs.
jq '{managed_paths: (.build_plan.managed_paths // []), generated_files: (.build_plan.generated_files // [])}' "$STAGING_STATE" > "$BASELINE"
echo "✓ Baseline snapshot written ($(jq '.managed_paths | length' "$BASELINE") managed paths)"

# Builder-Core (B1-B6) + Builder-Heavy (B7-B9), fully deterministic: no
# sub-agent delegation, no placeholder guessing. These invocations live
# INSIDE this block so _extract_phase concatenation yields an order-correct,
# self-contained script (baseline -> builders -> validation) instead of
# depending on prose steps between fences.
python3 "$WF_DIR/lib/builder-core.py" --state "$STAGING_STATE" --staging "$STAGING" --raw "${WF_RAW}" --wf-dir "$WF_DIR"
python3 "$WF_DIR/lib/builder-heavy.py" --state "$STAGING_STATE" --staging "$STAGING" --raw "${WF_RAW}" --wf-dir "$WF_DIR"

echo "✓ Builder finished — staging populated at $STAGING/"
```

**Instructions for the agent:** the block above is self-contained — it snapshots the baseline, runs Builder-Core and Builder-Heavy deterministically (`STAGING=".wizard-staging"`, `STAGING_STATE="$STAGING/wizard-state.json"`), and fails fast via `set -e`. The validation block below then verifies the staging set (B9/B9.5) before R4.

> **Important:** `lib/refresher.md`, `lib/builder.md`, `phase6a-agents.md`, and `phase6b-build-heavy.md` are **Markdown instruction files**, not bash scripts. Do not `source` them.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

STAGING=".wizard-staging"
STAGING_STATE="$STAGING/wizard-state.json"

if [[ ! -d "$STAGING" ]]; then
  echo "✗ $STAGING/ was not created."
  echo "  Builder (Phase R3) did not complete successfully."
  exit 1
fi

if [[ ! -f "$STAGING_STATE" ]]; then
  echo "✗ $STAGING_STATE not found — Builder must write state to staging."
  exit 1
fi

echo "=== Staging files ==="
find "$STAGING" -type f | sort
echo ""

echo "$(find "$STAGING" -type f | wc -l) files in $STAGING/"

# Validate staging state exists and has required fields
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
# into the IDE rules files in staging so R4's diff preview reflects the final content.
if [[ -f AGENTS.md ]] && [[ -f "$STAGING/AGENTS.md" ]]; then
  preserve_custom_agents "$STAGING"
fi
reinsert_legacy_bridge "$STAGING"

# Windsurf workflow setup (if applicable): /wf-init Phase 5 generates
# .windsurf/workflows/sdd-new.md at init time. Re-run the same substitution
# here so a refresh keeps it in sync with the current state (backend/project).
# Runs BEFORE the EXPECTED[] check below, which requires the file to exist.
IDES=$(jq -r '.answers.ides[]?' "$STAGING_STATE" 2>/dev/null)
if echo "$IDES" | grep -q "windsurf"; then
  if [[ -f "$WF_DIR/temp-files/sdd-new.md" ]]; then
    SDD_BACKEND=$(jq -r '.sdd.backend // "hybrid"' "$STAGING_STATE")
    PROJECT_NAME=$(jq -r '.answers.project_name' "$STAGING_STATE")
    SDD_PATH="$SDD_BACKEND"
    [ "$SDD_BACKEND" = "hybrid" ] && SDD_PATH="openspec"
    mkdir -p "$STAGING/.windsurf/workflows"
    cp "$WF_DIR/temp-files/sdd-new.md" "$STAGING/.windsurf/workflows/sdd-new.md"
    if [ "$SDD_BACKEND" = "engram" ]; then
      sed -i.bak "s|{{sdd.backend}}/changes/<name>/proposal.md|Engram memory:|g" "$STAGING/.windsurf/workflows/sdd-new.md"
    else
      sed -i.bak "s|{{sdd.backend}}/changes/|$SDD_PATH/changes/|g" "$STAGING/.windsurf/workflows/sdd-new.md"
    fi
    sed -i.bak "s/{{sdd.backend}}/$SDD_BACKEND/g" "$STAGING/.windsurf/workflows/sdd-new.md"
    sed -i.bak "s|{project}|$PROJECT_NAME|g" "$STAGING/.windsurf/workflows/sdd-new.md"
    rm -f "$STAGING/.windsurf/workflows/sdd-new.md.bak"
  else
    echo "⚠ $WF_DIR/temp-files/sdd-new.md not found; skipping .windsurf/workflows/sdd-new.md regeneration"
  fi
fi

# Dynamic EXPECTED[] validation: every artifact the features imply must exist in
# staging. A missing file means Builder-Core or Builder-Heavy did not run fully.
EXPECTED=()
IDES=$(jq -r '.answers.ides[]?' "$STAGING_STATE")
LADDER=$(jq -r '.features.decision_ladder' "$STAGING_STATE"); TDD=$(jq -r '.features.tdd_protocol' "$STAGING_STATE")
ROUTING=$(jq -r '.features.routing_abc' "$STAGING_STATE"); CI=$(jq -r '.features.ci' "$STAGING_STATE")
CD=$(jq -r '.features.cd' "$STAGING_STATE"); RELEASE=$(jq -r '.features.release_please' "$STAGING_STATE")
LAYERS=$(jq -r '.testing.layers[]?' "$STAGING_STATE")
[ "$LADDER" = "true" ] && EXPECTED+=(.agents/skills/wf-ladder/SKILL.md .agents/protocols/wf-ladder.md)
[ "$TDD" = "true" ] && [ -n "$LAYERS" ] && EXPECTED+=(.agents/skills/wf-tdd/SKILL.md .agents/protocols/wf-tdd.md)
[ "$ROUTING" = "true" ] && EXPECTED+=(.agents/skills/wf-sdd-trigger/SKILL.md .agents/protocols/wf-sdd-trigger.md)
# always-included commands are always present
EXPECTED+=(.agents/skills/wf-worktree/SKILL.md .agents/skills/wf-settings/SKILL.md .agents/skills/wf-onboard/SKILL.md)
for IDE in $IDES; do
  case "$IDE" in
    claude-code) EXPECTED+=(.claude/commands/wf-worktree.md .claude/commands/wf-settings.md .claude/commands/wf-onboard.md) ;;
    opencode)    EXPECTED+=(.opencode/commands/wf-worktree.md .opencode/commands/wf-settings.md .opencode/commands/wf-onboard.md) ;;
    cursor)      EXPECTED+=(.cursor/commands/wf-worktree.md .cursor/commands/wf-settings.md .cursor/commands/wf-onboard.md) ;;
    windsurf)    EXPECTED+=(.windsurf/workflows/wf-worktree.md .windsurf/workflows/wf-settings.md .windsurf/workflows/wf-onboard.md .windsurf/workflows/sdd-new.md) ;;
    kiro)        EXPECTED+=(.kiro/steering/wf-worktree.md .kiro/steering/wf-settings.md .kiro/steering/wf-onboard.md) ;;
    vscode-copilot) EXPECTED+=(.github/prompts/wf-worktree.prompt.md .github/prompts/wf-settings.prompt.md .github/prompts/wf-onboard.prompt.md) ;;
    codex)       EXPECTED+=(.codex/commands/wf-worktree.md .codex/commands/wf-settings.md .codex/commands/wf-onboard.md) ;;
  esac
done
[ "$CI" = "true" ] && EXPECTED+=(.github/workflows/quality-guard.yml)
[ "$RELEASE" = "true" ] && EXPECTED+=(.github/workflows/release-please.yml release-please-config.json .release-please-manifest.json .commitlintrc.json)
[ -n "$LAYERS" ] && EXPECTED+=(vitest.config.ts playwright.config.ts)
for f in "${EXPECTED[@]}"; do
  [ -f "$STAGING/$f" ] || { echo "✗ FAIL: missing $STAGING/$f — Builder-Core/Heavy did not run or failed"; exit 1; }
done
echo "✓ EXPECTED[] validation passed (${#EXPECTED[@]} artifacts)"

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

# Resume-marker gate: skip R4 when a resumed run targets a later phase.
_wf_resume_gate "R4"

STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")
PLAN="refresh-plan.json"

# Gate: fail loudly on unresolved wizard placeholders in staging. A previous
# build once escaped "{{version}}" into a committed .release-please-manifest.json;
# builder guidance says to abort on placeholders but nothing enforced it.
# Only wizard-owned placeholder namespaces are flagged — arbitrary "{{ }}"
# text (e.g. Vue/Angular interpolation quoted in project docs) is NOT a
# wizard placeholder and must not fail the refresh.
echo "ℹ Scanning staging for unresolved placeholders..."
PLACEHOLDER_HITS=$(grep -RInE '\{\{(answers|discovery|features|testing|mcps|protocols|conventions|stack)\.|\{\{(wizard_version|version)\}\}|\{\{PROTOCOL_BODY:' "$STAGING" 2>/dev/null || true)
# {{sdd.backend}} is scanned SEPARATELY with a narrow exemption: it doubles as
# a RUNTIME literal — the sed SEARCH PATTERN wf-settings uses to re-resolve the
# SDD backend when the user switches backends post-build — and builder-core.py
# ships it verbatim on purpose (see its NOTE in write_skills). Only occurrences
# OUTSIDE that sed-command context are unresolved-placeholder leaks. The
# exemption regex MUST use grep -E with escaped braces: BSD grep (macOS) gives
# undefined behavior for unescaped `{{` in BRE, so a fix validated only against
# GNU grep can pass CI and silently match nothing on macOS.
SDD_BACKEND_HITS=$(grep -RInE '\{\{sdd\.backend\}\}' "$STAGING" 2>/dev/null \
  | grep -vE 'sed[[:space:]].*s.[[:space:]]*\{\{sdd\.backend\}\}' || true)
if [[ -n "$PLACEHOLDER_HITS" && -n "$SDD_BACKEND_HITS" ]]; then
  PLACEHOLDER_HITS="${PLACEHOLDER_HITS}"$'\n'"${SDD_BACKEND_HITS}"
elif [[ -z "$PLACEHOLDER_HITS" && -n "$SDD_BACKEND_HITS" ]]; then
  PLACEHOLDER_HITS="$SDD_BACKEND_HITS"
fi
if [[ -n "$PLACEHOLDER_HITS" ]]; then
  echo "✗ Unresolved wizard placeholders found in $STAGING:" >&2
  echo "$PLACEHOLDER_HITS" >&2
  echo "  The Builder escaped template placeholders into final artifacts." >&2
  echo "  Fix the Builder output (or extend the allowlist above) before refreshing." >&2
  exit 1
fi
echo "✓ No unresolved placeholders in staging"

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
        # FU7: Check if the working tree file differs from HEAD (local modifications)
        local_modified=false
        if git rev-parse --verify HEAD >/dev/null 2>&1; then
          if ! git diff --quiet HEAD -- "$REL_PATH" 2>/dev/null; then
            local_modified=true
          fi
        else
          # No HEAD (non-git or fresh repo): compare against recorded old_hash from baseline
          OLD_HASH=$(jq -r --arg path "$REL_PATH" '.generated_files[] | select(.path == $path) | .hash' "$OLD_MANAGED" 2>/dev/null || true)
          if [[ -n "$OLD_HASH" && "$PROJECT_HASH" != "$OLD_HASH" ]]; then
            local_modified=true
          fi
        fi
        UPDATED=$(jq --arg path "$REL_PATH" --arg old_hash "$PROJECT_HASH" --arg new_hash "$STAGING_HASH" --argjson local_modified "$local_modified" '. += [{"path": $path, "old_hash": $old_hash, "new_hash": $new_hash, "local_modified": $local_modified}]' <<< "$UPDATED")
      fi
    else
      ADDED=$(jq --arg path "$REL_PATH" --arg hash "$STAGING_HASH" '. += [{"path": $path, "hash": $hash}]' <<< "$ADDED")
    fi
# Exclude git-internal files from the plan, with one exception: .git/hooks/post-commit
# is staged by the builder for non-Husky projects. Git refuses to commit paths inside
# .git/, but the refresh still must copy/chmod the hook and track it as a managed
# side-effect. The git-add/commit filters below already skip .git/ paths.
# Also exclude wizard-state.json: it is the staging state copy, never a project file.
done < <(
  find "$STAGING" -type f -not -path "*/.git/*" -not -name "wizard-state.json" -print0
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

# Explicit deprecated-path cleanup (Fix 3): these global-only command artifacts
# (installed by install.sh, never part of a project) must be removed even when
# they are NOT in the managed_paths baseline.
# FU4: Extended with per-IDE skill dirs for 6 deprecated commands (wf-cicd, wf-cleanup,
# wf-refresh, wf-init, wf-sdd-config, wf-sdd-lite) across 8 IDE skill roots.
DEPRECATED_COMMANDS=(wf-cicd wf-cleanup wf-refresh wf-init wf-sdd-config wf-sdd-lite)
IDE_SKILL_ROOTS=(.claude/skills .cursor/skills .opencode/skills .windsurf/skills .codex/skills .kiro/skills .github/skills)
# .devin/skills only when windsurf is active (per reinsert_legacy_bridge)
IDES=$(jq -r '.answers.ides[]?' "$WF_STATE" 2>/dev/null)
if echo "$IDES" | grep -q "windsurf"; then
  IDE_SKILL_ROOTS+=(.devin/skills)
fi

DEPRECATED_PATHS=(
  # Existing command artifacts (workflows/commands/prompts/protocols)
  .windsurf/workflows/wf-cicd.md .windsurf/workflows/wf-cleanup.md .windsurf/workflows/wf-refresh.md .windsurf/workflows/wf-init.md
  .claude/commands/wf-cicd.md .claude/commands/wf-cleanup.md .claude/commands/wf-refresh.md .claude/commands/wf-init.md
  .cursor/commands/wf-cicd.md .cursor/commands/wf-cleanup.md .cursor/commands/wf-refresh.md .cursor/commands/wf-init.md
  .opencode/commands/wf-cicd.md .opencode/commands/wf-cleanup.md .opencode/commands/wf-refresh.md .opencode/commands/wf-init.md
  .codex/commands/wf-cicd.md .codex/commands/wf-cleanup.md .codex/commands/wf-refresh.md .codex/commands/wf-init.md
  .kiro/steering/wf-cicd.md .kiro/steering/wf-cleanup.md .kiro/steering/wf-refresh.md .kiro/steering/wf-init.md
  .github/prompts/wf-cicd.prompt.md .github/prompts/wf-cleanup.prompt.md .github/prompts/wf-refresh.prompt.md .github/prompts/wf-init.prompt.md
  .agents/protocols/wf-cicd.md .agents/skills/wf-cicd/SKILL.md .agents/skills/wf-cleanup/SKILL.md .agents/skills/wf-refresh/SKILL.md .agents/skills/wf-init/SKILL.md
  .agents/skills/wf-sdd-config/SKILL.md .agents/protocols/wf-sdd-config.md
  # FU4: Per-IDE skill dirs for 6 deprecated commands
)
# Add per-IDE skill paths for all 6 deprecated commands
for cmd in "${DEPRECATED_COMMANDS[@]}"; do
  for root in "${IDE_SKILL_ROOTS[@]}"; do
    DEPRECATED_PATHS+=("$root/$cmd/SKILL.md")
  done
done

for dp in "${DEPRECATED_PATHS[@]}"; do
  if [ -f "$dp" ] && [ ! -f "$STAGING/$dp" ]; then
    DELETED=$(jq --arg path "$dp" --arg reason "deprecated command" '. += [{"path": $path, "reason": $reason}]' <<< "$DELETED")
  fi
done

# Deduplicate deletion paths (a path may appear both in the managed_paths
# baseline and in DEPRECATED_PATHS; unique_by keeps the counts honest).
DELETED=$(jq 'unique_by(.path)' <<< "$DELETED")
DELETED_MODIFIED=$(jq 'unique_by(.path)' <<< "$DELETED_MODIFIED")

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

if jq -e '.updated[]? | select(.path == "AGENTS.md")' "$PLAN" >/dev/null 2>&1; then
  echo "ℹ AGENTS.md will be regenerated from state.discovery. Fenced/tree-formatted Project Structure sections and backticked command descriptions are preserved/merged; if other sections still look flat, re-run /wf-init phase1 (discovery) before the next refresh."
fi

# The plan now holds the classified diff; the pre-Builder baseline is no longer
# needed. (R6's cleanup trap also removes it defensively.)
rm -f "$BASELINE"

echo "✓ Phase R4 complete"
```

---

## Phase R5: Review gate

Present the grouped diff and collect explicit user approvals for each category. Do NOT proceed to Phase R6 without approval.

### Non-interactive Resume Flow (FU5)

When running in non-interactive mode (no TTY, e.g., CI/CD, agent-driven), `_ask_yesno_safe` cannot prompt the user. Instead, it records pending prompts to `${WF_DIR}/.wizard-pending-prompts` and returns exit code 3. Pre-R5 phases (R1/R2) treat a recorded prompt as a hard stop via `_require_answer_or_stop`: they emit the manifest immediately and write `.wizard-resume-phase`, so a resumed run re-enters exactly the phase that asked and the answer is consumed by its owner. Phase R5 batches its OWN review prompts the same way: unanswered ones accumulate during the review and are emitted as ONE manifest (plus `apply_mode`) before any approval is stored, so a runner supplies every answer in a single pass. The legacy collection sweep remains as a safety net for pre-R5 leftovers:

```
GENTLE_AI_WF_REFRESH_NEEDS=prompt=<prompt1>|prompt=<prompt2>|...|apply_mode=<mode>
```

To resume:
1. Read the manifest (from stdout or env var)
2. Set `WF_REFRESH_ANSWERS` with `prompt=yes|prompt=no|...` pairs (joined by `|`)
3. Set `WF_REFRESH_APPLY_MODE` to `commit`, `apply-only`, or `cancel`
4. Re-run with `WF_REFRESH_RESUME=1`

**Important**: Phase R-1 (global commands) also supports resume — if it had a pending prompt, it will consume the answer from `WF_REFRESH_ANSWERS` on resume. All phases share the same manifest/answer mechanism.

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

PLAN="refresh-plan.json"
STAGING=$(jq -r '.build_plan.staging_dir // ".wizard-staging"' "$WF_STATE")

# FU5: Handle WF_REFRESH_RESUME=1 — skip R-1..R4, re-enter R5 with staging intact.
# The manifest from a previous non-tty run emitted GENTLE_AI_WF_REFRESH_NEEDS with exit 3.
# On resume, validate that staging/plan exist and proceed directly to R5 review.
if [[ "${WF_REFRESH_RESUME:-}" = "1" ]]; then
  if [[ ! -d "$STAGING" ]] || [[ ! -f "$PLAN" ]]; then
    echo "ERROR: WF_REFRESH_RESUME=1 but staging ($STAGING) or plan ($PLAN) missing." >&2
    echo "  Cannot resume — run full /wf-refresh instead." >&2
    exit 1
  fi
  echo "ℹ Resuming at R5 (WF_REFRESH_RESUME=1) — staging and plan validated."
  # Consume a marker left by the review-prompt hard stop so this exact phase
  # re-entered. The R-1..R4 resume gates already skipped via that same marker.
  if [[ -f "${WF_DIR}/.wizard-resume-phase" ]] \
     && [[ "$(cat "${WF_DIR}/.wizard-resume-phase")" = "R5" ]]; then
    rm -f "${WF_DIR}/.wizard-resume-phase"
    echo "ℹ Resuming at R5 (review gate)"
  fi
else
  # FU5: Collect pending prompts from all phases and emit manifest if any.
  pending_file="${WF_DIR}/.wizard-pending-prompts"
  if [[ -f "$pending_file" ]]; then
    prompts=()
    mapfile -t prompts < "$pending_file"
    if [[ ${#prompts[@]} -gt 0 ]]; then
      # Build manifest: prompt=<p1>|prompt=<p2>|...|apply_mode=...
      manifest=""
      apply_mode="${WF_REFRESH_APPLY_MODE:-}"
      for p in "${prompts[@]}"; do
        manifest+="prompt=${p}|"
      done
      if [[ -n "$apply_mode" ]]; then
        manifest+="apply_mode=${apply_mode}"
      else
        manifest="${manifest%|}"  # trim trailing |
      fi
      echo "GENTLE_AI_WF_REFRESH_NEEDS=${manifest}"
      # Clean up pending file for next run
      rm -f "$pending_file"
      echo "✗ Non-tty run requires answers for ${#prompts[@]} prompt(s)." >&2
      echo "  Set WF_REFRESH_ANSWERS or WF_REFRESH_DEFAULT_ANSWER and re-run with WF_REFRESH_RESUME=1." >&2
      exit 3
    fi
    # No pending prompts, clean up
    rm -f "$pending_file"
  fi
fi

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
APPROVE_OVERWRITE_LOCAL="false"

# R5 review ask. Unlike the pre-R5 fail-fast gates, unanswered prompts here do
# NOT abort one-by-one: they accumulate in R5_PENDING and, once every category
# has been asked, ONE combined manifest is emitted listing everything still
# missing plus apply_mode. A runner can then supply all answers in a single
# WF_REFRESH_ANSWERS batch instead of one round-trip per question.
R5_PENDING=()
_r5_ask() {
  local prompt="$1" var="$2" rc=0
  _ask_yesno_safe "$prompt" || rc=$?
  case "$rc" in
    0) printf -v "$var" '%s' "true" ;;
    1) printf -v "$var" '%s' "false" ;;
    3)
      R5_PENDING+=("$prompt")
      printf -v "$var" '%s' "false"
      ;;
    *) printf -v "$var" '%s' "false" ;;
  esac
}

if [[ $ADDED_COUNT -gt 0 ]]; then
  _r5_ask "Apply added files?" APPROVE_ADDED
fi

if [[ $UPDATED_COUNT -gt 0 ]]; then
  _r5_ask "Apply updated files?" APPROVE_UPDATED
fi

if [[ $DELETED_COUNT -gt 0 ]]; then
  _r5_ask "Delete removed files?" APPROVE_DELETED
fi

if [[ $DELETED_MODIFIED_COUNT -gt 0 ]]; then
  echo "The following files are wizard-managed but were modified by you."
  echo "Deleting them may lose your changes."
  jq -r '.deleted_modified[] | "  - \(.path)"' "$PLAN"
  _r5_ask "Delete these modified files?" APPROVE_DELETED_MODIFIED
fi

# FU7: Dedicated warning block for locally-modified updated files
LOCAL_MODIFIED_COUNT=$(jq '[.updated[]? | select(.local_modified == true)] | length' "$PLAN")
if [[ $LOCAL_MODIFIED_COUNT -gt 0 ]]; then
  echo ""
  echo "⚠️  LOCALLY-MODIFIED UPDATED FILES ($LOCAL_MODIFIED_COUNT) — working tree differs from HEAD:"
  jq -r '.updated[]? | select(.local_modified == true) | "  - \(.path)"' "$PLAN"
  echo ""
  echo "These files have uncommitted changes. Overwriting them will lose your local edits."
  _r5_ask "Overwrite locally-modified files?" APPROVE_OVERWRITE_LOCAL
else
  APPROVE_OVERWRITE_LOCAL="false"
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
  _r5_ask "Append these .gitignore entries and include them in the commit?" APPROVE_GITIGNORE
fi

# Emit ONE manifest listing every still-unanswered review prompt plus the
# pending apply decision, then stop. Resume re-enters exactly here (marker
# below); prompts already satisfied from WF_REFRESH_ANSWERS drop off the list,
# so the run converges in as few round-trips as the runner's answers allow.
if [[ ${#R5_PENDING[@]} -gt 0 ]]; then
  printf '%s\n' "R5" > "${WF_DIR}/.wizard-resume-phase"
  manifest=""
  for p in "${R5_PENDING[@]}"; do manifest+="prompt=${p}|"; done
  manifest+="apply_mode=${WF_REFRESH_APPLY_MODE:-}"
  echo "GENTLE_AI_WF_REFRESH_NEEDS=${manifest}"
  echo "✗ Non-tty run requires ${#R5_PENDING[@]} answer(s) and WF_REFRESH_APPLY_MODE before applying." >&2
  echo "  Set WF_REFRESH_ANSWERS='<prompt>=yes|<prompt>=no|...' and" >&2
  echo "  WF_REFRESH_APPLY_MODE=commit|apply-only|cancel, then re-run with WF_REFRESH_RESUME=1." >&2
  exit 3
fi

# Store approvals in staging state
STAGING_STATE="$STAGING/wizard-state.json"
jq --argjson added "$APPROVE_ADDED" \
   --argjson updated "$APPROVE_UPDATED" \
   --argjson deleted "$APPROVE_DELETED" \
   --argjson deleted_modified "$APPROVE_DELETED_MODIFIED" \
   --argjson gitignore "$APPROVE_GITIGNORE" \
   --argjson overwrite_local "$APPROVE_OVERWRITE_LOCAL" \
   '.build_plan.approval = {added: $added, updated: $updated, deleted: $deleted, deleted_modified: $deleted_modified, gitignore: $gitignore, overwrite_local: $overwrite_local} | .updated_at = (now | todate)' "$STAGING_STATE" > "$STAGING_STATE.tmp"
mv "$STAGING_STATE.tmp" "$STAGING_STATE"

# Explicit confirmation gate before R6: apply+commit, apply without commit, or cancel.
echo ""
echo "=== RESUMEN DE APROBACIONES ==="
echo "  Added: $APPROVE_ADDED"
echo "  Updated: $APPROVE_UPDATED"
echo "  Deleted: $APPROVE_DELETED"
echo "  Deleted-modified: $APPROVE_DELETED_MODIFIED"
echo "  Gitignore: $APPROVE_GITIGNORE"
echo "  Overwrite local: $APPROVE_OVERWRITE_LOCAL"
echo ""
echo "¿Cómo aplicar los cambios aprobados?"
if [[ ! -t 0 ]]; then
  # Non-tty (agent-driven): WF_REFRESH_APPLY_MODE must name the choice.
  case "${WF_REFRESH_APPLY_MODE:-}" in
    commit) APPLY_CHOICE="1" ;;
    apply-only) APPLY_CHOICE="2" ;;
    cancel) APPLY_CHOICE="3" ;;
    *)
      # Same contract as every other gate: NEEDS marker + exit 3. A bare
      # exit 2 here used to bypass automated runners listening for
      # GENTLE_AI_WF_REFRESH_NEEDS entirely.
      echo "GENTLE_AI_WF_REFRESH_NEEDS=apply_mode="
      echo "ERROR: non-interactive apply gate requires WF_REFRESH_APPLY_MODE=commit|apply-only|cancel." >&2
      echo "  Aborting: refusing to guess. No changes were applied." >&2
      exit 3
      ;;
  esac
  echo "(non-interactive — WF_REFRESH_APPLY_MODE=${WF_REFRESH_APPLY_MODE:-})"
else
  while true; do
    read -r -p "Opción [1=commit / 2=sin commit / 3=cancelar] (default 1): " APPLY_CHOICE
    APPLY_CHOICE="${APPLY_CHOICE:-1}"
    case "$APPLY_CHOICE" in
      1|2|3) break ;;
      *) echo "  Opción inválida: '$APPLY_CHOICE' (use 1, 2 o 3)" ;;
    esac
  done
fi
case "$APPLY_CHOICE" in
    1)
      echo "✓ Procediendo a Phase R6 (aplicar + commit)..."
      ;;
    2)
      echo "✓ Modo aplicar-sin-commit: los archivos se copiarán al working tree"
      echo "  pero NO se creará ningún commit. Revisa y commitea cuando quieras."
      jq '.build_plan.apply_only = true | .updated_at = (now | todate)' "$STAGING_STATE" > "$STAGING_STATE.tmp"
      mv "$STAGING_STATE.tmp" "$STAGING_STATE"
      ;;
    3)
      echo "✗ Refresh cancelado por el usuario. No se aplicaron cambios."
      rm -rf "$STAGING"
      rm -f "$PLAN" .wizard-refresh-baseline.json
      exit 0
      ;;
esac

echo "✓ Phase R5 complete"
```

---

## Phase R6: Apply and close

Copy approved changes, update state, write `.wizard-managed-files.json`, commit, and close.
**Reads approvals from staging state (`.wizard-staging/wizard-state.json`); promotes to root on success.**

```bash
#!/bin/bash
set -e

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
source "${WF_DIR}/lib/refresh-lib.sh"

STAGING=".wizard-staging"
STAGING_STATE="$STAGING/wizard-state.json"
PLAN="refresh-plan.json"

# Ensure staging, plan, and the R3 baseline are removed even if R6 fails.
cleanup_r6() {
  rm -rf "$STAGING"
  rm -f "$PLAN"
  rm -f .wizard-refresh-baseline.json
}
trap cleanup_r6 EXIT

echo "ℹ Applying approved changes..."

# Read approvals from STAGING STATE (not root)
APPROVE_ADDED=$(jq -r '.build_plan.approval.added // false' "$STAGING_STATE")
APPROVE_UPDATED=$(jq -r '.build_plan.approval.updated // false' "$STAGING_STATE")
APPROVE_DELETED=$(jq -r '.build_plan.approval.deleted // false' "$STAGING_STATE")
APPROVE_DELETED_MODIFIED=$(jq -r '.build_plan.approval.deleted_modified // false' "$STAGING_STATE")
APPROVE_GITIGNORE=$(jq -r '.build_plan.approval.gitignore // false' "$STAGING_STATE")
# FU7: Overwrite locally-modified files approval
APPROVE_OVERWRITE_LOCAL=$(jq -r '.build_plan.approval.overwrite_local // false' "$STAGING_STATE")
# Apply-only mode: copy approved files to the working tree but do NOT stage or commit.
APPLY_ONLY=$(jq -r '.build_plan.apply_only // false' "$STAGING_STATE")

# Preserve custom AGENTS.md sections BEFORE any copy: the project AGENTS.md still
# holds the user's custom markers here, and the staged AGENTS.md is the freshly
# generated plain version. If this ran after the copy loops, the project file
# would already be overwritten and preservation would silently no-op.
if [[ "$APPROVE_UPDATED" == "true" ]] || [[ "$APPROVE_ADDED" == "true" ]]; then
  if [[ -f AGENTS.md ]] && [[ -f "$STAGING/AGENTS.md" ]]; then
    preserve_custom_agents "$STAGING"
  fi
  # Reinsert the Windsurf/Devin legacy path bridge into the IDE rules files
  # so the approved copy carries it, the manifest hashes it, and a declined refresh
  # writes nothing. Idempotent: skipped when the rule is already present.
  reinsert_legacy_bridge "$STAGING"
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
    # FU7: Skip local-modified files unless overwrite_local approval is given
    local_modified=$(jq -r --arg path "$file" '.updated[]? | select(.path == $path) | .local_modified // false' "$PLAN")
    if [[ "$local_modified" == "true" && "$APPROVE_OVERWRITE_LOCAL" != "true" ]]; then
      echo "  ⏭ Skipping locally-modified file (no overwrite approval): $file"
      continue
    fi
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
    if [[ "$APPLY_ONLY" == "true" ]]; then
      # FU6: Apply-only mode uses plain rm (unstaged)
      while IFS= read -r -d '' file; do
        rm -f "$file"
      done < "$DELETED_LIST"
    else
      # Commit mode uses git rm (staged)
      git rm -f --ignore-unmatch --pathspec-from-file="$DELETED_LIST" --pathspec-file-nul
    fi
  fi
  rm -f "$DELETED_LIST"
  echo "✓ Files deleted"
fi

if [[ "$APPROVE_DELETED_MODIFIED" == "true" ]]; then
  echo "ℹ Deleting modified-removed files..."
  DELETED_MODIFIED_LIST=$(mktemp)
  jq -j '.deleted_modified[]?.path + "\u0000"' "$PLAN" > "$DELETED_MODIFIED_LIST"
  if [ -s "$DELETED_MODIFIED_LIST" ]; then
    if [[ "$APPLY_ONLY" == "true" ]]; then
      # FU6: Apply-only mode uses plain rm (unstaged)
      while IFS= read -r -d '' file; do
        rm -f "$file"
      done < "$DELETED_MODIFIED_LIST"
    else
      # Commit mode uses git rm (staged)
      git rm -f --ignore-unmatch --pathspec-from-file="$DELETED_MODIFIED_LIST" --pathspec-file-nul
    fi
  fi
  rm -f "$DELETED_MODIFIED_LIST"
  echo "✓ Modified-removed files deleted"
fi

# Git operations (only if any category was approved). In apply-only mode we still
# compute the manifest and update state, but we do NOT stage or commit.
if [[ "$APPROVE_ADDED" == "true" ]] || [[ "$APPROVE_UPDATED" == "true" ]] || [[ "$APPROVE_DELETED" == "true" ]] || [[ "$APPROVE_DELETED_MODIFIED" == "true" ]] || [[ "$APPROVE_GITIGNORE" == "true" ]]; then
  echo "ℹ $(if [[ "$APPLY_ONLY" == "true" ]]; then echo "Applying changes to the working tree (no commit)"; else echo "Committing changes..."; fi)"

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

  # Update state build_plan. Write to the STAGING state so the final
  # `cp "$STAGING_STATE" "$WF_STATE"` promotes the complete, recomputed plan
  # (writing to root here would be silently overwritten by that cp).
  jq --argjson files "$GENERATED_FILES" --argjson paths "$MANAGED_PATHS" \
     '.build_plan.generated_files = $files | .build_plan.managed_paths = $paths | .updated_at = (now | todate)' "$STAGING_STATE" > "$STAGING_STATE.tmp"
  mv "$STAGING_STATE.tmp" "$STAGING_STATE"

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
        claude-code) _gi_add "!.claude/"; _gi_add "!CLAUDE.md" ;;
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

  # Stage and commit only when not in apply-only mode (apply-only leaves the
  # changes unstaged in the working tree for the user to review and commit).
  if [[ "$APPLY_ONLY" != "true" ]]; then
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
    # Commit message via temp file to avoid nested heredoc parsing issues (zsh/bash)
    COMMIT_MSG_FILE=$(mktemp)
    cat > "$COMMIT_MSG_FILE" <<MSG_EOF
chore: refresh workflow to v$TARGET_VERSION

- Updated AGENTS.md with new project info
- Added $(jq '.added | length' "$PLAN") new files
- Updated $(jq '.updated | length' "$PLAN") files
- Removed $(jq '.deleted | length' "$PLAN") deprecated files
- Removed $(jq '.deleted_modified | length' "$PLAN") modified-deprecated files

Generated with /wf-refresh
MSG_EOF
    COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")
    rm -f "$COMMIT_MSG_FILE"

    # git diff does NOT support --pathspec-from-file (usage error 129); read the
    # approved paths into positional arguments so the guard is portable.
    COMMIT_PATH_ARGS=()
    while IFS= read -r -d '' p; do
      COMMIT_PATH_ARGS+=("$p")
    done < "$COMMIT_PATHS"

    # FU7: Support WF_REFRESH_SKIP_TESTS to skip husky pre-commit hooks (e.g., npm test)
    # Useful for CI/automation where tests run separately. Default: run hooks.
    SKIP_TESTS="${WF_REFRESH_SKIP_TESTS:-false}"
    COMMIT_FLAGS=""
    if [[ "$SKIP_TESTS" = "true" ]]; then
      COMMIT_FLAGS="--no-verify"
      echo "ℹ Skipping pre-commit hooks (WF_REFRESH_SKIP_TESTS=true)"
    fi

    if git diff --cached --quiet -- "${COMMIT_PATH_ARGS[@]}"; then
      echo "ℹ Approved paths have no staged changes; skipping commit"
    else
      git commit $COMMIT_FLAGS -m "$COMMIT_MSG" --pathspec-from-file="$COMMIT_PATHS" --pathspec-file-nul
    fi
  else
    echo "ℹ No approved paths to commit"
  fi
  else
    echo "ℹ Apply-only mode: changes left in the working tree (unstaged)."
    echo "  Review with: git status && git diff"
  fi
else
  echo "ℹ No changes approved; skipping commit (no files were written)"
fi

# Promote staging state to root (single source of truth for next refresh).
# apply_only is a per-run decision: drop it so the promoted state stays clean.
if [[ "$APPROVE_ADDED" == "true" ]] || [[ "$APPROVE_UPDATED" == "true" ]] || [[ "$APPROVE_DELETED" == "true" ]] || [[ "$APPROVE_DELETED_MODIFIED" == "true" ]] || [[ "$APPROVE_GITIGNORE" == "true" ]]; then
  if [[ "$APPLY_ONLY" == "true" ]]; then
    jq 'del(.build_plan.apply_only)' "$STAGING_STATE" > "$STAGING_STATE.tmp"
    mv "$STAGING_STATE.tmp" "$STAGING_STATE"
  fi
  cp "$STAGING_STATE" "$WF_STATE"
  echo "✓ State promoted from staging to root"
fi

# Staging and plan are cleaned by the EXIT trap installed above.

echo "✓ Phase R6 complete"
if [[ "$APPLY_ONLY" == "true" ]]; then
  echo "ℹ Apply-only: changes left in the working tree (unstaged). Review with: git status && git diff"
else
  echo "ℹ Next: git push (when ready)"
fi
```

---

## End of /wf-refresh

After Phase R6, the refresh is complete. Verify with:

```bash
git log -1 -p
```
