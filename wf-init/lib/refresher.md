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

cat > "${WF_DIR}/lib/refresh-lib.sh" << 'LIBEOF'
#!/bin/bash
# Pure bash helper library for /wf-refresh.
# No Markdown files are sourced here.

WF_DIR="${WF_DIR:-/tmp/wf-refresh-phases}"
WF_STATE="${WF_STATE:-.wizard-state.json}"
WF_RAW="${WF_RAW:-https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main}"

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
  if [[ "$v1" == "$v2" ]]; then
    return 1
  fi
  version_lte "$v1" "$v2"
}

# Fetch current wizard version from remote, falling back to a local file or default.
wf_fetch_version() {
  local version=""
  version=$(curl -fsSL "${WF_RAW}/VERSION" 2>/dev/null | head -1 || true)
  if [[ -z "$version" ]]; then
    if [[ -f VERSION ]]; then
      version=$(head -1 VERSION)
    else
      version="0.7.1-beta.1"
    fi
  fi
  printf '%s' "$version"
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
  local filter="$1"
  local tmp="${WF_STATE}.tmp"
  jq "$filter" "$WF_STATE" > "$tmp" && mv "$tmp" "$WF_STATE"
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

# Compute SHA256 hash of a file.
wf_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
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
if [[ -f AGENTS.md ]]; then
  LOCAL_VERSION=$(sed -n 's/.*wf-version: \([^ |]*\).*/\1/p' AGENTS.md | tail -1)
fi
if [[ -z "$LOCAL_VERSION" ]]; then
  LOCAL_VERSION=$(jq -r '.wizard_version // empty' "$WF_STATE" 2>/dev/null || true)
fi
LOCAL_VERSION="${LOCAL_VERSION:-0.1.0-beta.1}"
LOCAL_VERSION="${LOCAL_VERSION#v}"

echo "ℹ Local wizard version: $LOCAL_VERSION"

REMOTE_VERSION=$(curl -s "${WF_RAW}/VERSION" 2>/dev/null | head -1 || true)
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
[[ -d .claude ]] && IDES+=("claude")
[[ -d .cursor ]] && IDES+=("cursor")
[[ -d .windsurf ]] && IDES+=("windsurf")
[[ -d .devin ]] && IDES+=("devin")
[[ -d .kiro ]] && IDES+=("kiro")
[[ -d .codex ]] && IDES+=("codex")
[[ -d .opencode ]] && IDES+=("opencode")
[[ -f .github/copilot-instructions.md ]] && IDES+=("vscode-copilot")

if [[ ${#IDES[@]} -eq 0 ]]; then
  echo "⚠ No active IDEs detected"
else
  echo "ℹ Detected IDEs: ${IDES[*]}"
fi

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
    pkg_framework=$(jq -r '.dependencies.next // .dependencies.vue // empty' package.json 2>/dev/null || true)
    [[ -n "$pkg_framework" ]] && STACK_KEY="node-$(basename "$pkg_framework")"
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
    _apply_jq_filter ".discovery.stack_key = \"$STACK_KEY\" | .discovery.node_engine = \"$NODE_ENGINE\" | .discovery.git_commits = $GIT_COMMITS"
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

**Instructions for the agent:**

1. Use the same Builder sub-agent delegation as `/wf-init` Phase 6:
   - Read `phase6a-agents.md` first. If your environment supports it (e.g. Claude Code `task` tool, Devin `run_subagent` tool), delegate Builder-Core to a sub-agent with the prompt from `subagent-builder-core.md`.
   - Otherwise, read `lib/builder.md` and execute B1-B6 manually.
2. After Builder-Core completes, read `phase6b-build-heavy.md` and run Builder-Heavy (B7-B9) the same way.
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

for artifact in AGENTS.md .wizard-state.json; do
  if [[ ! -f "$STAGING/$artifact" ]]; then
    echo "✗ Missing critical artifact: $STAGING/$artifact"
    exit 1
  fi
done

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

# Scan staging files
for file in $(find "$STAGING" -type f); do
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
done

# Scan old managed paths for deletions
OLD_MANAGED=$(jq -r '.build_plan.managed_paths[]?' "$WF_STATE" 2>/dev/null || true)
for old_path in $OLD_MANAGED; do
  if [[ ! -f "$STAGING/$old_path" ]]; then
    if [[ -f "$old_path" ]]; then
      PROJECT_HASH=$(wf_sha256 "$old_path")
      OLD_HASH=$(jq -r ".build_plan.generated_files[] | select(.path == \"$old_path\") | .hash" "$WF_STATE" 2>/dev/null || true)

      if [[ "$PROJECT_HASH" == "$OLD_HASH" ]]; then
        DELETED=$(jq --arg path "$old_path" --arg hash "$PROJECT_HASH" '. += [{"path": $path, "hash": $hash, "reason": "deprecated"}]' <<< "$DELETED")
      else
        DELETED_MODIFIED=$(jq --arg path "$old_path" --arg old_hash "$OLD_HASH" --arg project_hash "$PROJECT_HASH" '. += [{"path": $path, "old_hash": $old_hash, "project_hash": $project_hash, "reason": "deprecated (user modified)"}]' <<< "$DELETED_MODIFIED")
      fi
    fi
  fi
done

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

echo "ℹ Applying approved changes..."

APPROVE_ADDED=$(jq -r '.build_plan.approval.added // false' "$WF_STATE")
APPROVE_UPDATED=$(jq -r '.build_plan.approval.updated // false' "$WF_STATE")
APPROVE_DELETED=$(jq -r '.build_plan.approval.deleted // false' "$WF_STATE")
APPROVE_DELETED_MODIFIED=$(jq -r '.build_plan.approval.deleted_modified // false' "$WF_STATE")

if [[ "$APPROVE_ADDED" == "true" ]]; then
  echo "ℹ Copying added files..."
  jq -r '.added[] | .path' "$PLAN" | while read -r file; do
    mkdir -p "$(dirname "$file")"
    cp "$STAGING/$file" "$file"
    [[ "$file" == *".sh" ]] && chmod +x "$file"
  done
  echo "✓ Added files copied"
fi

if [[ "$APPROVE_UPDATED" == "true" ]]; then
  echo "ℹ Updating files..."
  jq -r '.updated[] | .path' "$PLAN" | while read -r file; do
    cp "$STAGING/$file" "$file"
    [[ "$file" == *".sh" ]] && chmod +x "$file"
  done
  echo "✓ Files updated"
fi

if [[ "$APPROVE_DELETED" == "true" ]]; then
  echo "ℹ Deleting removed files..."
  jq -r '.deleted[] | .path' "$PLAN" | while read -r file; do
    rm -f "$file"
  done
  echo "✓ Files deleted"
fi

if [[ "$APPROVE_DELETED_MODIFIED" == "true" ]]; then
  echo "ℹ Deleting modified-removed files..."
  jq -r '.deleted_modified[] | .path' "$PLAN" | while read -r file; do
    rm -f "$file"
  done
  echo "✓ Modified-removed files deleted"
fi

# Preserve custom AGENTS.md sections in the staged AGENTS.md before copy
if [[ "$APPROVE_UPDATED" == "true" ]] || [[ "$APPROVE_ADDED" == "true" ]]; then
  if [[ -f AGENTS.md ]] && [[ -f "$STAGING/AGENTS.md" ]]; then
    preserve_custom_agents "$STAGING"
  fi
fi

# Recompute generated_files from actual staging after custom-section injection
GENERATED_FILES="[]"
MANAGED_PATHS="[]"
for file in $(find "$STAGING" -type f); do
  REL_PATH="${file#$STAGING/}"
  HASH=$(wf_sha256 "$file")
  GENERATED_FILES=$(jq --arg path "$REL_PATH" --arg hash "$HASH" '. += [{"path": $path, "hash": $hash, "managed": true}]' <<< "$GENERATED_FILES")
  MANAGED_PATHS=$(jq --arg path "$REL_PATH" '. += [$path]' <<< "$MANAGED_PATHS")
done

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

# Add to .gitignore
if ! grep -q "^\.wizard-managed-files\.json$" .gitignore 2>/dev/null; then
  echo ".wizard-managed-files.json" >> .gitignore
fi

# Git operations (only if any category was approved)
if [[ "$APPROVE_ADDED" == "true" ]] || [[ "$APPROVE_UPDATED" == "true" ]] || [[ "$APPROVE_DELETED" == "true" ]] || [[ "$APPROVE_DELETED_MODIFIED" == "true" ]]; then
  echo "ℹ Committing changes..."
  git add -A

  COMMIT_MSG="chore: refresh workflow to v$TARGET_VERSION

- Updated AGENTS.md with new project info
- Added $(jq '.added | length' "$PLAN") new files
- Updated $(jq '.updated | length' "$PLAN") files
- Removed $(jq '.deleted | length' "$PLAN") deprecated files
- Removed $(jq '.deleted_modified | length' "$PLAN") modified-deprecated files

Generated with /wf-refresh"

  git commit -m "$COMMIT_MSG" 2>/dev/null || {
    echo "⚠ No changes to commit"
  }
else
  echo "ℹ No changes approved; skipping commit"
fi

# Clean staging and plan
rm -rf "$STAGING"
rm -f "$PLAN"

echo "✓ Phase R6 complete"
echo "ℹ Next: git push (when ready)"
```

---

## End of /wf-refresh

After Phase R6, the refresh is complete. Verify with:

```bash
git log -1 -p
```
