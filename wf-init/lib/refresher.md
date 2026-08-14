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
source "${WF_DIR}/lib/state-helpers.sh" 2>/dev/null || true

# Fallback portable sha256 if the shared helper is unavailable.
if ! command -v wf_sha256 >/dev/null 2>&1; then
  wf_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum "$1" | awk '{print $1}'
    else
      shasum -a 256 "$1" | awk '{print $1}'
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
    printf '%s' "${version#v}"
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

  if (( m1 != m2 )); then
    (( m1 < m2 )) && return 0 || return 1
  fi
  if (( n1 != n2 )); then
    (( n1 < n2 )) && return 0 || return 1
  fi
  if (( p1 != p2 )); then
    (( p1 < p2 )) && return 0 || return 1
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

# Ask a yes/no question. Returns 0 for yes, 1 for no.
_ask_yesno() {
  local prompt="$1"
  local reply
  read -p "$prompt [y/n] " -n 1 -r reply
  echo
  if [[ "$reply" =~ ^[Yy]$ ]]; then
    return 0
  else
    return 1
  fi
}

# Apply a single state migration block idempotently using jq.
# Writes a .tmp file and moves it into place.
_apply_jq_filter() {
  local filter="${@: -1}"
  local args=("${@:1:$#-1}")
  local tmp="${WF_STATE}.tmp"
  jq "${args[@]}" "$filter" "$WF_STATE" > "$tmp" && mv "$tmp" "$WF_STATE"
}

# Migration to v0.6.8: schema v3 fields + new optional features.
migrate_to_0_6_8() {
  echo "  Migrating state to v0.6.8..."

  # Schema v3 fields
  _apply_jq_filter '
    .schema_version = 3 |
    .build_plan.generated_files //= [] |
    .build_plan.managed_paths //= [] |
    .build_plan.approval //= {}
  '

  # Ask about new optional features (idempotent: only if missing)
  if ! jq -e '.features.routing_abc' "$WF_STATE" >/dev/null 2>&1; then
    if _ask_yesno "Enable ABC routing pattern?"; then
      _apply_jq_filter '.features.routing_abc = true'
    else
      _apply_jq_filter '.features.routing_abc = false'
    fi
  fi

  if ! jq -e '.features.decision_ladder' "$WF_STATE" >/dev/null 2>&1; then
    if _ask_yesno "Enable decision ladder?"; then
      _apply_jq_filter '.features.decision_ladder = true'
    else
      _apply_jq_filter '.features.decision_ladder = false'
    fi
  fi

  # CI/CD defaults
  _apply_jq_filter '
    .ci.e2e_in_ci //= false |
    .ci.auto_improve //= true |
    .ci.inline_suggestions //= true
  '
}

# Migration to v0.7.0: no new schema fields, just version bump handled by caller.
migrate_to_0_7_0() {
  echo "  Migrating state to v0.7.0..."
  # No schema changes for v0.7.0 in this release.
  :
}

# Migration to v0.7.1: no new schema fields in this release.
migrate_to_0_7_1() {
  echo "  Migrating state to v0.7.1..."
  # No schema changes for v0.7.1 in this release.
  :
}

# Migrate state from CURRENT_VERSION to TARGET_VERSION using cumulative migrations.
migrate_state() {
  local CURRENT_VERSION="$1"
  local TARGET_VERSION="$2"

  if ! version_lt "$CURRENT_VERSION" "$TARGET_VERSION"; then
    echo "  No migration needed: $CURRENT_VERSION already >= $TARGET_VERSION"
    return 0
  fi

  echo "  Migrating state from $CURRENT_VERSION to $TARGET_VERSION..."

  local CURRENT="$CURRENT_VERSION"

  # List of known migration target versions in ascending order.
  local MIGRATIONS=("0.6.8" "0.7.0" "0.7.1-beta.1" "0.7.1")

  local TO
  for TO in "${MIGRATIONS[@]}"; do
    if version_lt "$CURRENT" "$TO" && version_lte "$TO" "$TARGET_VERSION"; then
      case "$TO" in
        0.6.8) migrate_to_0_6_8 ;;
        0.7.0) migrate_to_0_7_0 ;;
        0.7.1-beta.1) migrate_to_0_7_1 ;;
        0.7.1) migrate_to_0_7_1 ;;
      esac
      CURRENT="$TO"
    fi
  done

  # Always write the exact target version at the end.
  _apply_jq_filter ".wizard_version = \"$TARGET_VERSION\""
  echo "  ✓ State migrated to $TARGET_VERSION"
}

# Ensure custom AGENTS.md sections are preserved.
# Reads existing AGENTS.md, extracts blocks between markers, and re-injects them
# into the staged AGENTS.md at the same relative position.
preserve_custom_agents() {
  local STAGING="${1:-.wizard-staging}"
  local PROJECT_AGENTS="AGENTS.md"
  local STAGED_AGENTS="${STAGING}/AGENTS.md"

  if [[ ! -f "$PROJECT_AGENTS" ]] || [[ ! -f "$STAGED_AGENTS" ]]; then
    return 0
  fi

  # Idempotent: if the Builder already preserved the custom markers into the
  # staged AGENTS.md, do NOT re-inject (avoids duplicating the section).
  if grep -q "<!-- WF: DO NOT REGENERATE -->" "$STAGED_AGENTS"; then
    echo "  ℹ Custom sections already present in staged AGENTS.md (Builder preserved them)"
    return 0
  fi

  echo "  Preserving custom AGENTS.md sections..."

  local TMP="${STAGED_AGENTS}.tmp"
  local IN_CUSTOM=false
  local CUSTOM_BLOCK=""
  local LINE

  while IFS= read -r LINE; do
    if [[ "$LINE" == *"<!-- WF: DO NOT REGENERATE -->"* ]]; then
      IN_CUSTOM=true
      CUSTOM_BLOCK="${LINE}"$'\n'
      continue
    fi
    if [[ "$LINE" == *"<!-- /WF: DO NOT REGENERATE -->"* ]]; then
      IN_CUSTOM=false
      CUSTOM_BLOCK="${CUSTOM_BLOCK}${LINE}"$'\n'
      # Inject into staged file at the same heading level? Simpler: append before first "##".
      # If no "##", append at end.
      if grep -q '^## ' "$STAGED_AGENTS"; then
        local HEADING
        HEADING=$(grep -n '^## ' "$STAGED_AGENTS" | head -1 | cut -d: -f1)
        {
          head -n "$((HEADING - 1))" "$STAGED_AGENTS"
          printf '\n%s\n' "$CUSTOM_BLOCK"
          tail -n "+$HEADING" "$STAGED_AGENTS"
        } > "$TMP"
        mv "$TMP" "$STAGED_AGENTS"
      else
        printf '\n%s\n' "$CUSTOM_BLOCK" >> "$STAGED_AGENTS"
      fi
      CUSTOM_BLOCK=""
      continue
    fi
    if $IN_CUSTOM; then
      CUSTOM_BLOCK="${CUSTOM_BLOCK}${LINE}"$'\n'
    fi
  done < "$PROJECT_AGENTS"

  echo "  ✓ Custom sections preserved"
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
if [[ -f AGENTS.md ]]; then
  LOCAL_VERSION=$(sed -n 's/.*wf-version: \([^ |]*\).*/\1/p' AGENTS.md | tail -1)
fi
if [[ -z "$LOCAL_VERSION" ]]; then
  LOCAL_VERSION=$(jq -r '.wizard_version // empty' "$WF_STATE" 2>/dev/null || true)
fi
LOCAL_VERSION="${LOCAL_VERSION:-0.1.0-beta.1}"
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
  read -p "Update global commands? [y/n] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ -f install.sh ]]; then
      echo "ℹ Running install.sh..."
      bash install.sh || echo "⚠ install.sh failed; continuing anyway"
    else
      echo "⚠ install.sh not found; skipping update"
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

IDES_JSON=$(printf '%s\n' "${IDES[@]}" | jq -R . | jq -s .)
_apply_jq_filter --argjson ides "$IDES_JSON" '.answers.ides = $ides'

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

GIT_COMMITS=$(git log --oneline 2>/dev/null | wc -l || echo "0")

OLD_STACK=$(jq -r '.discovery.stack_key // ""' "$WF_STATE")
OLD_NODE=$(jq -r '.discovery.node_engine // ""' "$WF_STATE")

if [[ "$OLD_STACK" != "$STACK_KEY" ]] || [[ "$OLD_NODE" != "$NODE_ENGINE" ]]; then
  echo "⚠ Project content drift detected:"
  [[ "$OLD_STACK" != "$STACK_KEY" ]] && echo "  - Stack: $OLD_STACK → $STACK_KEY"
  [[ "$OLD_NODE" != "$NODE_ENGINE" ]] && echo "  - Node engine: $OLD_NODE → $NODE_ENGINE"

  read -p "Use updated project info? [y/n] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    _apply_jq_filter \
      --arg stack_key "$STACK_KEY" \
      --arg node_engine "$NODE_ENGINE" \
      --argjson git_commits "$GIT_COMMITS" \
      '.discovery.stack_key = $stack_key | .discovery.node_engine = $node_engine | .discovery.git_commits = $git_commits'
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

CURRENT_VERSION=$(jq -r '.wizard_version // "0.1.0-beta.1"' "$WF_STATE")
CURRENT_VERSION="${CURRENT_VERSION#v}"

TARGET_VERSION=$(wf_fetch_version)
TARGET_VERSION="${TARGET_VERSION#v}"

echo "ℹ Current state version: $CURRENT_VERSION"
echo "ℹ Target version: $TARGET_VERSION"

migrate_state "$CURRENT_VERSION" "$TARGET_VERSION"

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
   - When replacing placeholders in the sub-agent prompt, use `{WF_PATH}` → `$WF_DIR` (the downloaded phase directory, e.g. `/tmp/wf-refresh-phases`). The helper `lib/state-helpers.sh` lives directly under `$WF_DIR/lib/`.
   - Otherwise, read `lib/builder.md` and execute B1-B6 manually.
2. After Builder-Core completes, read `phase6b-build-heavy.md` and run Builder-Heavy (B7-B9) the same way — **execute ONLY its steps 1-4 (verify staging, delegate, fallback, validate). Do NOT execute phase6b's Step 5 tail**: no `wf_phase_done phase6 phase7`, no "Wait for user confirmation", and NO `cat "$WF_DIR/phase7.md"`. Those belong to the `/wf-init` phase 7/8 flow, not to refresh — running them would derail into wf-init's review/promotion instead of returning to Phase R4. After Builder-Heavy validates, return to Phase R4 below.
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
done < <(find "$STAGING" -type f -print0)

# Deletion baseline: the R3 Step 0 snapshot (pre-Builder). Fall back to the live
# state only when the snapshot is missing (e.g. running R4 standalone).
BASELINE=".wizard-refresh-baseline.json"
if [[ -f "$BASELINE" ]]; then
  OLD_MANAGED_SRC="$BASELINE"
  OLD_FILES_SRC="$BASELINE"
else
  OLD_MANAGED_SRC="$WF_STATE"
  OLD_FILES_SRC="$WF_STATE"
fi

# Scan old managed paths for deletions (null-delimited for paths with spaces/newlines).
while IFS= read -r -d '' old_path; do
  if [[ ! -f "$STAGING/$old_path" ]]; then
    if [[ -f "$old_path" ]]; then
      PROJECT_HASH=$(wf_sha256 "$old_path")
      OLD_HASH=$(jq -r --arg path "$old_path" '.generated_files[] | select(.path == $path) | .hash' "$OLD_FILES_SRC" 2>/dev/null || true)

      if [[ "$PROJECT_HASH" == "$OLD_HASH" ]]; then
        DELETED=$(jq --arg path "$old_path" --arg hash "$PROJECT_HASH" '. += [{"path": $path, "hash": $hash, "reason": "deprecated"}]' <<< "$DELETED")
      else
        DELETED_MODIFIED=$(jq --arg path "$old_path" --arg old_hash "$OLD_HASH" --arg project_hash "$PROJECT_HASH" '. += [{"path": $path, "old_hash": $old_hash, "project_hash": $project_hash, "reason": "deprecated (user modified)"}]' <<< "$DELETED_MODIFIED")
      fi
    fi
  fi
done < <(jq -j '.managed_paths[]? + "\u0000"' "$OLD_MANAGED_SRC" 2>/dev/null || true)

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

APPROVE_ADDED="false"
APPROVE_UPDATED="false"
APPROVE_DELETED="false"
APPROVE_DELETED_MODIFIED="false"

if [[ $ADDED_COUNT -gt 0 ]]; then
  read -p "Apply added files? [y/n] " -n 1 -r
  echo
  [[ $REPLY =~ ^[Yy]$ ]] && APPROVE_ADDED="true"
fi

if [[ $UPDATED_COUNT -gt 0 ]]; then
  read -p "Apply updated files? [y/n] " -n 1 -r
  echo
  [[ $REPLY =~ ^[Yy]$ ]] && APPROVE_UPDATED="true"
fi

if [[ $DELETED_COUNT -gt 0 ]]; then
  read -p "Delete removed files? [y/n] " -n 1 -r
  echo
  [[ $REPLY =~ ^[Yy]$ ]] && APPROVE_DELETED="true"
fi

if [[ $DELETED_MODIFIED_COUNT -gt 0 ]]; then
  echo "The following files are wizard-managed but were modified by you."
  echo "Deleting them may lose your changes."
  jq -r '.deleted_modified[] | "  - \(.path)"' "$PLAN"
  read -p "Delete these modified files? [y/n] " -n 1 -r
  echo
  [[ $REPLY =~ ^[Yy]$ ]] && APPROVE_DELETED_MODIFIED="true"
fi

# Store approvals in state
jq --argjson added "$APPROVE_ADDED" \
   --argjson updated "$APPROVE_UPDATED" \
   --argjson deleted "$APPROVE_DELETED" \
   --argjson deleted_modified "$APPROVE_DELETED_MODIFIED" \
   '.build_plan.approval = {added: $added, updated: $updated, deleted: $deleted, deleted_modified: $deleted_modified}' "$WF_STATE" > "$WF_STATE.tmp"
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

# Preserve custom AGENTS.md sections BEFORE any copy: the project AGENTS.md still
# holds the user's custom markers here, and the staged AGENTS.md is the freshly
# generated plain version. If this ran after the copy loops, the project file
# would already be overwritten and preservation would silently no-op.
if [[ "$APPROVE_UPDATED" == "true" ]] || [[ "$APPROVE_ADDED" == "true" ]]; then
  if [[ -f AGENTS.md ]] && [[ -f "$STAGING/AGENTS.md" ]]; then
    preserve_custom_agents "$STAGING"
  fi
fi

if [[ "$APPROVE_ADDED" == "true" ]]; then
  echo "ℹ Copying added files..."
  while IFS= read -r -d '' file; do
    mkdir -p "$(dirname "$file")"
    cp "$STAGING/$file" "$file"
    [[ "$file" == *".sh" ]] && chmod +x "$file"
  done < <(jq -j '.added[]?.path + "\u0000"' "$PLAN")
  echo "✓ Added files copied"
fi

if [[ "$APPROVE_UPDATED" == "true" ]]; then
  echo "ℹ Updating files..."
  while IFS= read -r -d '' file; do
    cp "$STAGING/$file" "$file"
    [[ "$file" == *".sh" ]] && chmod +x "$file"
  done < <(jq -j '.updated[]?.path + "\u0000"' "$PLAN")
  echo "✓ Files updated"
fi

if [[ "$APPROVE_DELETED" == "true" ]]; then
  echo "ℹ Deleting removed files..."
  DELETED_LIST=$(mktemp)
  jq -j '.deleted[]?.path + "\u0000"' "$PLAN" > "$DELETED_LIST"
  if [ -s "$DELETED_LIST" ]; then
    git rm --pathspec-from-file="$DELETED_LIST" --pathspec-file-nul
  fi
  rm -f "$DELETED_LIST"
  echo "✓ Files deleted"
fi

if [[ "$APPROVE_DELETED_MODIFIED" == "true" ]]; then
  echo "ℹ Deleting modified-removed files..."
  DELETED_MODIFIED_LIST=$(mktemp)
  jq -j '.deleted_modified[]?.path + "\u0000"' "$PLAN" > "$DELETED_MODIFIED_LIST"
  if [ -s "$DELETED_MODIFIED_LIST" ]; then
    git rm --pathspec-from-file="$DELETED_MODIFIED_LIST" --pathspec-file-nul
  fi
  rm -f "$DELETED_MODIFIED_LIST"
  echo "✓ Modified-removed files deleted"
fi

# Git operations (only if any category was approved)
if [[ "$APPROVE_ADDED" == "true" ]] || [[ "$APPROVE_UPDATED" == "true" ]] || [[ "$APPROVE_DELETED" == "true" ]] || [[ "$APPROVE_DELETED_MODIFIED" == "true" ]]; then
  echo "ℹ Committing changes..."

  # Recompute generated_files from actual staging after custom-section injection,
  # then persist the refresh bookkeeping. This runs ONLY when at least one
  # category was approved: a fully declined refresh must not write
  # .wizard-managed-files.json, touch .gitignore, or update the build plan.
  GENERATED_FILES="[]"
  MANAGED_PATHS="[]"
  while IFS= read -r -d '' file; do
    REL_PATH="${file#$STAGING/}"
    HASH=$(wf_sha256 "$file")
    GENERATED_FILES=$(jq --arg path "$REL_PATH" --arg hash "$HASH" '. += [{"path": $path, "hash": $hash, "managed": true}]' <<< "$GENERATED_FILES")
    MANAGED_PATHS=$(jq --arg path "$REL_PATH" '. += [$path]' <<< "$MANAGED_PATHS")
  done < <(find "$STAGING" -type f -print0)

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
     '.build_plan.generated_files = $files | .build_plan.managed_paths = $paths' "$WF_STATE" > "$WF_STATE.tmp"
  mv "$WF_STATE.tmp" "$WF_STATE"

  # Add to .gitignore (ensure a trailing newline first and use an exact line match).
  GITIGNORE_MODIFIED=false
  if ! grep -qxF ".wizard-managed-files.json" .gitignore 2>/dev/null; then
    if [ -f .gitignore ] && [ "$(tail -c1 .gitignore | wc -l)" -eq 0 ]; then
      echo >> .gitignore
    fi
    printf '%s\n' ".wizard-managed-files.json" >> .gitignore
    GITIGNORE_MODIFIED=true
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
    jq -j '.added[]?.path + "\u0000"' "$PLAN" >> "$GIT_ADD_LIST"
  fi
  if [[ "$APPROVE_UPDATED" == "true" ]]; then
    jq -j '.updated[]?.path + "\u0000"' "$PLAN" >> "$GIT_ADD_LIST"
  fi
  if [ "$GITIGNORE_MODIFIED" = true ]; then
    printf '.gitignore\0' >> "$GIT_ADD_LIST"
  fi
  if [ -s "$GIT_ADD_LIST" ]; then
    git add --pathspec-from-file="$GIT_ADD_LIST" --pathspec-file-nul
  fi
  rm -f "$GIT_ADD_LIST"

  # Commit exactly the approved paths (working-tree content). Other pre-staged
  # user files stay in the index and are NOT included in this commit.
  COMMIT_PATHS=$(mktemp)
  if [[ "$APPROVE_ADDED" == "true" ]]; then
    jq -j '.added[]?.path + "\u0000"' "$PLAN" >> "$COMMIT_PATHS"
  fi
  if [[ "$APPROVE_UPDATED" == "true" ]]; then
    jq -j '.updated[]?.path + "\u0000"' "$PLAN" >> "$COMMIT_PATHS"
  fi
  if [[ "$APPROVE_DELETED" == "true" ]]; then
    jq -j '.deleted[]?.path + "\u0000"' "$PLAN" >> "$COMMIT_PATHS"
  fi
  if [[ "$APPROVE_DELETED_MODIFIED" == "true" ]]; then
    jq -j '.deleted_modified[]?.path + "\u0000"' "$PLAN" >> "$COMMIT_PATHS"
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

    if git diff --cached --quiet --pathspec-from-file="$COMMIT_PATHS" --pathspec-file-nul; then
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
