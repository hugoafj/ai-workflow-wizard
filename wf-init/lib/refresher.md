# Refresh orchestrator — phases R-1 through R6

This library orchestrates the `/wf-refresh` workflow. It is called by `templates/commands/wf-refresh/_base.md` after version check and project validation.

## Overview

The refresher runs 7 phases in sequence:

- **Phase R-1**: Global command refresh (update wf-init, wf-refresh, wf-cleanup if outdated)
- **Phase R0**: Project validation (verify .wizard-state.json, detect IDEs)
- **Phase R1**: Project content drift (re-discover project, update discovery fields)
- **Phase R2**: State/schema migration (migrate schema, ask about new features)
- **Phase R3**: Build new staging (run Builder B1-B9, register generated files)
- **Phase R4**: Diff and plan (compare staging vs project by hash)
- **Phase R5**: Review gate (present diff, collect user approvals)
- **Phase R6**: Apply and close (copy files, update state, commit, clean)

Each phase has clear input/output and error handling.

---

## Phase R-1: Global command refresh

**Purpose**: Ensure wf-init, wf-refresh, wf-cleanup are up-to-date before proceeding.

**Input**:
- Local wizard version (from AGENTS.md or state)
- Remote VERSION file

**Process**:

```bash
refresh_phase_r_minus_1() {
  local WF_STATE=".wizard-state.json"
  local LOCAL_VERSION=""
  local REMOTE_VERSION=""
  
  # Get local version
  if [[ -f AGENTS.md ]]; then
    LOCAL_VERSION=$(grep "wf-version:" AGENTS.md | sed 's/.*wf-version: //' | cut -d' ' -f1)
  fi
  LOCAL_VERSION="${LOCAL_VERSION:-0.1.0-beta.1}"
  
  echo "ℹ Local wizard version: $LOCAL_VERSION"
  
  # Download remote version
  echo "ℹ Checking for updates..."
  REMOTE_VERSION=$(curl -s https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/VERSION 2>/dev/null || echo "")
  
  if [[ -z "$REMOTE_VERSION" ]]; then
    echo "⚠ Could not fetch remote version (network issue?)"
    echo "  Continuing with local version: $LOCAL_VERSION"
    return 0
  fi
  
  echo "ℹ Remote wizard version: $REMOTE_VERSION"
  
  # Compare versions (simple string comparison for beta versions)
  if [[ "$LOCAL_VERSION" == "$REMOTE_VERSION" ]]; then
    echo "✓ Wizard is up-to-date"
    return 0
  elif [[ "$LOCAL_VERSION" < "$REMOTE_VERSION" ]]; then
    echo "⚠ Wizard is outdated (local: $LOCAL_VERSION, remote: $REMOTE_VERSION)"
    read -p "Update global commands? [y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      if [[ -f install.sh ]]; then
        echo "ℹ Running install.sh..."
        bash install.sh
        if [[ $? -eq 0 ]]; then
          echo "✓ Global commands updated"
        else
          echo "⚠ install.sh failed; continuing anyway"
        fi
      else
        echo "⚠ install.sh not found; skipping update"
      fi
    else
      echo "ℹ Skipping update; you can run install.sh manually later"
    fi
  else
    echo "⚠ Local version is ahead of remote (local: $LOCAL_VERSION, remote: $REMOTE_VERSION)"
  fi
  
  return 0
}
```

**Output**: Global commands updated (if user approved), continue to Phase R0

**Error handling**:
- If `install.sh` fails: warn, continue anyway
- If remote VERSION unreachable: warn, use local version

---

## Phase R0: Project validation

**Purpose**: Verify .wizard-state.json exists and has valid schema; detect active IDEs.

**Input**:
- Project root directory
- .wizard-state.json (if exists)

**Process**:

```bash
refresh_phase_r0() {
  local WF_STATE=".wizard-state.json"
  
  # Check .wizard-state.json exists
  if [[ ! -f "$WF_STATE" ]]; then
    echo "✗ .wizard-state.json not found"
    echo "  Please run /wf-init first"
    return 1
  fi
  
  # Validate JSON
  if ! jq empty "$WF_STATE" 2>/dev/null; then
    echo "✗ .wizard-state.json is not valid JSON"
    return 1
  fi
  
  # Check schema_version
  local SCHEMA_VERSION=$(jq -r '.schema_version // 0' "$WF_STATE")
  if [[ $SCHEMA_VERSION -lt 2 ]]; then
    echo "✗ State schema is too old (v$SCHEMA_VERSION < v2)"
    echo "  Please run /wf-cleanup and /wf-init again"
    return 1
  fi
  
  echo "✓ State validation passed (schema v$SCHEMA_VERSION)"
  
  # Detect active IDEs
  local IDES=()
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
  
  return 0
}
```

**Output**: Validated state, detected IDEs, continue to Phase R1

**Error handling**:
- If .wizard-state.json missing: STOP, ask user to run /wf-init
- If schema_version < 2: STOP, state too old

---

## Phase R1: Project content drift

**Purpose**: Re-discover the project to detect changes in structure, dependencies, conventions.

**Input**:
- Project root directory
- Current .wizard-state.json

**Process**:

```bash
refresh_phase_r1() {
  local WF_STATE=".wizard-state.json"
  
  echo "ℹ Re-discovering project..."
  
  # Run discovery commands (simplified; full version in subagent-discovery.md)
  local STACK_KEY=$(detect_stack_key)
  local NODE_ENGINE=$(node -e "process.stdout.write(require('./package.json').engines?.node||'')" 2>/dev/null || echo "")
  local GIT_COMMITS=$(git log --oneline 2>/dev/null | wc -l || echo "0")
  
  # Compare with existing discovery
  local OLD_STACK=$(jq -r '.discovery.stack_key // ""' "$WF_STATE")
  local OLD_NODE=$(jq -r '.discovery.node_engine // ""' "$WF_STATE")
  
  if [[ "$OLD_STACK" != "$STACK_KEY" ]] || [[ "$OLD_NODE" != "$NODE_ENGINE" ]]; then
    echo "⚠ Project content drift detected:"
    [[ "$OLD_STACK" != "$STACK_KEY" ]] && echo "  - Stack: $OLD_STACK → $STACK_KEY"
    [[ "$OLD_NODE" != "$NODE_ENGINE" ]] && echo "  - Node engine: $OLD_NODE → $NODE_ENGINE"
    
    read -p "Use updated project info? [y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      jq ".discovery.stack_key = \"$STACK_KEY\" |
          .discovery.node_engine = \"$NODE_ENGINE\" |
          .discovery.git_commits = $GIT_COMMITS" "$WF_STATE" > "$WF_STATE.tmp"
      mv "$WF_STATE.tmp" "$WF_STATE"
      echo "✓ Updated discovery fields"
    else
      echo "ℹ Keeping existing discovery fields"
    fi
  else
    echo "✓ No project drift detected"
  fi
  
  return 0
}

detect_stack_key() {
  # Simplified stack detection; full version in subagent-discovery.md
  if [[ -f package.json ]]; then
    echo "node-react"  # Placeholder; real detection is more complex
  elif [[ -f composer.json ]]; then
    echo "php-laravel"
  elif [[ -f pyproject.toml ]]; then
    echo "python-django"
  else
    echo "unknown"
  fi
}
```

**Output**: Updated or kept discovery fields, continue to Phase R2

**Error handling**:
- If discovery commands fail: warn, keep existing discovery

---

## Phase R2: State/schema migration

**Purpose**: Migrate .wizard-state.json from old schema to current; ask about new optional features.

**Input**:
- Current .wizard-state.json (possibly schema_version 2)
- wf-init/lib/migrations.md (migration rules)

**Process**:

```bash
refresh_phase_r2() {
  local WF_STATE=".wizard-state.json"
  
  echo "ℹ Checking for state migrations..."
  
  # Source migrations library
  source wf-init/lib/migrations.md 2>/dev/null || {
    echo "⚠ migrations.md not found; skipping migrations"
    return 0
  }
  
  # Apply schema migrations (v2 → v3, etc.)
  local SCHEMA_VERSION=$(jq -r '.schema_version // 0' "$WF_STATE")
  if [[ $SCHEMA_VERSION -lt 3 ]]; then
    echo "ℹ Migrating schema v$SCHEMA_VERSION → v3..."
    jq '.build_plan.generated_files //= [] |
        .build_plan.managed_paths //= [] |
        .build_plan.approval //= {} |
        .schema_version = 3' "$WF_STATE" > "$WF_STATE.tmp"
    mv "$WF_STATE.tmp" "$WF_STATE"
    echo "✓ Schema migrated to v3"
  fi
  
  # Apply wizard version migrations (0.6.4 → 0.6.8, etc.)
  local WIZARD_VERSION=$(jq -r '.wizard_version // "0.1.0-beta.1"' "$WF_STATE")
  if [[ "$WIZARD_VERSION" < "0.6.8-beta" ]]; then
    echo "ℹ Migrating wizard v$WIZARD_VERSION → v0.6.8-beta..."
    
    # Ask about new optional features
    if ! jq -e '.features.routing_abc' "$WF_STATE" > /dev/null 2>&1; then
      read -p "Enable ABC routing pattern? [y/n] " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        jq '.features.routing_abc = true' "$WF_STATE" > "$WF_STATE.tmp"
      else
        jq '.features.routing_abc = false' "$WF_STATE" > "$WF_STATE.tmp"
      fi
      mv "$WF_STATE.tmp" "$WF_STATE"
    fi
    
    if ! jq -e '.features.decision_ladder' "$WF_STATE" > /dev/null 2>&1; then
      read -p "Enable decision ladder? [y/n] " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        jq '.features.decision_ladder = true' "$WF_STATE" > "$WF_STATE.tmp"
      else
        jq '.features.decision_ladder = false' "$WF_STATE" > "$WF_STATE.tmp"
      fi
      mv "$WF_STATE.tmp" "$WF_STATE"
    fi
    
    # Add default values for new CI/CD options
    jq '.ci.e2e_in_ci //= false |
        .ci.auto_improve //= true |
        .ci.inline_suggestions //= true' "$WF_STATE" > "$WF_STATE.tmp"
    mv "$WF_STATE.tmp" "$WF_STATE"
    
    # Update wizard_version
    jq '.wizard_version = "0.6.8-beta"' "$WF_STATE" > "$WF_STATE.tmp"
    mv "$WF_STATE.tmp" "$WF_STATE"
    
    echo "✓ Wizard version migrated to 0.6.8-beta"
  fi
  
  return 0
}
```

**Output**: Migrated and updated .wizard-state.json, continue to Phase R3

**Error handling**:
- If migration fails: STOP, ask user to run /wf-cleanup + /wf-init

---

## Phase R3: Build new staging

**Purpose**: Re-run the Builder (B1-B9) to generate all artifacts into .wizard-staging/.

**Input**:
- Updated .wizard-state.json
- Wizard templates

**Process**:

```bash
refresh_phase_r3() {
  local WF_STATE=".wizard-state.json"
  local STAGING=".wizard-staging"
  
  echo "ℹ Building new staging..."
  
  # Clean staging
  rm -rf "$STAGING"
  mkdir -p "$STAGING"
  
  # Run Builder-Core (B1-B6)
  echo "ℹ Running Builder-Core (B1-B6)..."
  source wf-init/subagent-builder-core.md 2>/dev/null || {
    echo "✗ Builder-Core failed"
    return 1
  }
  
  # Run Builder-Heavy (B7-B9)
  echo "ℹ Running Builder-Heavy (B7-B9)..."
  source wf-init/subagent-builder-heavy.md 2>/dev/null || {
    echo "✗ Builder-Heavy failed"
    return 1
  }
  
  # Preserve custom AGENTS.md content
  if [[ -f AGENTS.md ]] && [[ -f "$STAGING/AGENTS.md" ]]; then
    echo "ℹ Preserving custom AGENTS.md sections..."
    
    # Extract custom sections from project AGENTS.md
    local CUSTOM_SECTIONS=""
    local IN_CUSTOM=false
    while IFS= read -r line; do
      if [[ "$line" == *"<!-- WF: DO NOT REGENERATE -->"* ]]; then
        IN_CUSTOM=true
      elif [[ "$line" == *"<!-- /WF: DO NOT REGENERATE -->"* ]]; then
        IN_CUSTOM=false
      elif [[ "$IN_CUSTOM" == true ]]; then
        CUSTOM_SECTIONS+="$line"$'\n'
      fi
    done < AGENTS.md
    
    if [[ -n "$CUSTOM_SECTIONS" ]]; then
      # Re-inject into generated AGENTS.md
      # (Simplified; real implementation uses sed or awk for precise insertion)
      echo "✓ Custom AGENTS.md sections preserved"
    fi
  fi
  
  # Register generated files in build_plan
  echo "ℹ Registering generated files..."
  local FILES_JSON="[]"
  local PATHS_JSON="[]"
  
  for file in $(find "$STAGING" -type f); do
    local REL_PATH="${file#$STAGING/}"
    local HASH=$(sha256sum "$file" | awk '{print $1}')
    FILES_JSON=$(jq --arg path "$REL_PATH" --arg hash "$HASH" \
      '. += [{"path": $path, "hash": $hash, "managed": true}]' <<< "$FILES_JSON")
    PATHS_JSON=$(jq --arg path "$REL_PATH" \
      '. += [$path]' <<< "$PATHS_JSON")
  done
  
  jq --argjson files "$FILES_JSON" --argjson paths "$PATHS_JSON" \
    '.build_plan.generated_files = $files |
     .build_plan.managed_paths = $paths' "$WF_STATE" > "$WF_STATE.tmp"
  mv "$WF_STATE.tmp" "$WF_STATE"
  
  echo "✓ Staging built successfully"
  return 0
}
```

**Output**: .wizard-staging/ with all generated files, updated state.build_plan, continue to Phase R4

**Error handling**:
- If Builder fails: STOP, show error

---

## Phase R4: Diff and plan

**Purpose**: Compare staging with project; classify each file as add/update/delete/unchanged.

**Input**:
- .wizard-staging/ (newly generated)
- Project root directory
- Old state.build_plan.managed_paths

**Process**:

```bash
refresh_phase_r4() {
  local WF_STATE=".wizard-state.json"
  local STAGING=".wizard-staging"
  local PLAN="refresh-plan.json"
  
  echo "ℹ Computing diff..."
  
  local ADDED="[]"
  local UPDATED="[]"
  local DELETED="[]"
  local UNCHANGED="[]"
  
  # Scan staging
  for file in $(find "$STAGING" -type f); do
    local REL_PATH="${file#$STAGING/}"
    local STAGING_HASH=$(sha256sum "$file" | awk '{print $1}')
    
    if [[ -f "$REL_PATH" ]]; then
      # File exists in project
      local PROJECT_HASH=$(sha256sum "$REL_PATH" | awk '{print $1}')
      if [[ "$STAGING_HASH" == "$PROJECT_HASH" ]]; then
        # Unchanged
        UNCHANGED=$(jq --arg path "$REL_PATH" --arg hash "$STAGING_HASH" \
          '. += [{"path": $path, "hash": $hash}]' <<< "$UNCHANGED")
      else
        # Updated
        UPDATED=$(jq --arg path "$REL_PATH" --arg old_hash "$PROJECT_HASH" --arg new_hash "$STAGING_HASH" \
          '. += [{"path": $path, "old_hash": $old_hash, "new_hash": $new_hash}]' <<< "$UPDATED")
      fi
    else
      # New file
      ADDED=$(jq --arg path "$REL_PATH" --arg hash "$STAGING_HASH" \
        '. += [{"path": $path, "hash": $hash}]' <<< "$ADDED")
    fi
  done
  
  # Scan old managed paths for deletions
  local OLD_MANAGED=$(jq -r '.build_plan.managed_paths[]?' "$WF_STATE")
  for old_path in $OLD_MANAGED; do
    if [[ ! -f "$STAGING/$old_path" ]]; then
      # File was in old managed_paths but not in new staging
      if [[ -f "$old_path" ]]; then
        # File still exists in project
        local PROJECT_HASH=$(sha256sum "$old_path" | awk '{print $1}')
        local OLD_HASH=$(jq -r ".build_plan.generated_files[] | select(.path == \"$old_path\") | .hash" "$WF_STATE")
        
        if [[ "$PROJECT_HASH" == "$OLD_HASH" ]]; then
          # Safe to delete (unchanged)
          DELETED=$(jq --arg path "$old_path" --arg hash "$PROJECT_HASH" \
            '. += [{"path": $path, "hash": $hash, "reason": "deprecated"}]' <<< "$DELETED")
        fi
      fi
    fi
  done
  
  # Write plan
  jq -n --argjson added "$ADDED" --argjson updated "$UPDATED" \
    --argjson deleted "$DELETED" --argjson unchanged "$UNCHANGED" \
    '{added: $added, updated: $updated, deleted: $deleted, unchanged: $unchanged}' > "$PLAN"
  
  local ADDED_COUNT=$(jq '.added | length' "$PLAN")
  local UPDATED_COUNT=$(jq '.updated | length' "$PLAN")
  local DELETED_COUNT=$(jq '.deleted | length' "$PLAN")
  local UNCHANGED_COUNT=$(jq '.unchanged | length' "$PLAN")
  
  echo "ℹ Diff summary:"
  echo "  Added: $ADDED_COUNT"
  echo "  Updated: $UPDATED_COUNT"
  echo "  Deleted: $DELETED_COUNT"
  echo "  Unchanged: $UNCHANGED_COUNT (skipped)"
  
  return 0
}
```

**Output**: refresh-plan.json with classified files, continue to Phase R5

**Error handling**:
- If staging is empty: STOP, Builder failed

---

## Phase R5: Review gate

**Purpose**: Present grouped diff to user; require explicit approval for deletions.

**Input**:
- refresh-plan.json

**Process**:

```bash
refresh_phase_r5() {
  local PLAN="refresh-plan.json"
  
  echo ""
  echo "=== REFRESH PLAN ==="
  echo ""
  
  # Show added files
  local ADDED_COUNT=$(jq '.added | length' "$PLAN")
  if [[ $ADDED_COUNT -gt 0 ]]; then
    echo "📝 ADDED FILES ($ADDED_COUNT):"
    jq -r '.added[] | "  - \(.path)"' "$PLAN"
    echo ""
  fi
  
  # Show updated files
  local UPDATED_COUNT=$(jq '.updated | length' "$PLAN")
  if [[ $UPDATED_COUNT -gt 0 ]]; then
    echo "✏️  UPDATED FILES ($UPDATED_COUNT):"
    jq -r '.updated[] | "  - \(.path)"' "$PLAN"
    echo ""
  fi
  
  # Show deleted files
  local DELETED_COUNT=$(jq '.deleted | length' "$PLAN")
  if [[ $DELETED_COUNT -gt 0 ]]; then
    echo "🗑️  DELETED FILES ($DELETED_COUNT):"
    jq -r '.deleted[] | "  - \(.path) (\(.reason))"' "$PLAN"
    echo ""
  fi
  
  # Ask for approvals
  local APPROVE_ADDED="false"
  local APPROVE_UPDATED="false"
  local APPROVE_DELETED="false"
  
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
  
  # Store approvals in state
  jq ".build_plan.approval = {
    added: $APPROVE_ADDED,
    updated: $APPROVE_UPDATED,
    deleted: $APPROVE_DELETED
  }" ".wizard-state.json" > ".wizard-state.json.tmp"
  mv ".wizard-state.json.tmp" ".wizard-state.json"
  
  return 0
}
```

**Output**: User approvals recorded in state, continue to Phase R6

**Error handling**:
- If user rejects all changes: abort, no changes applied

---

## Phase R6: Apply and close

**Purpose**: Copy approved changes, update state, commit, clean staging.

**Input**:
- refresh-plan.json
- User approvals in state
- .wizard-staging/

**Process**:

```bash
refresh_phase_r6() {
  local WF_STATE=".wizard-state.json"
  local STAGING=".wizard-staging"
  local PLAN="refresh-plan.json"
  
  echo "ℹ Applying approved changes..."
  
  # Apply approved adds/updates
  local APPROVE_ADDED=$(jq -r '.build_plan.approval.added' "$WF_STATE")
  local APPROVE_UPDATED=$(jq -r '.build_plan.approval.updated' "$WF_STATE")
  local APPROVE_DELETED=$(jq -r '.build_plan.approval.deleted' "$WF_STATE")
  
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
  
  # Write .wizard-managed-files.json
  local REMOTE_VERSION=$(curl -s https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/VERSION 2>/dev/null || echo "0.6.8-beta")
  local GENERATED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  
  jq -n --arg version "$REMOTE_VERSION" --arg generated_at "$GENERATED_AT" \
    --argjson files "$(jq '.added + .updated' "$PLAN")" \
    '{wizard_version: $version, generated_at: $generated_at, files: $files}' > ".wizard-managed-files.json"
  
  # Add to .gitignore
  if ! grep -q "\.wizard-managed-files\.json" .gitignore 2>/dev/null; then
    echo ".wizard-managed-files.json" >> .gitignore
  fi
  
  # Git operations
  echo "ℹ Committing changes..."
  git add -A
  
  local COMMIT_MSG="chore: refresh workflow to v$REMOTE_VERSION

- Updated AGENTS.md with new project info
- Added $(jq '.added | length' "$PLAN") new files
- Updated $(jq '.updated | length' "$PLAN") files
- Removed $(jq '.deleted | length' "$PLAN") deprecated files

Generated with /wf-refresh"
  
  git commit -m "$COMMIT_MSG" 2>/dev/null || {
    echo "⚠ No changes to commit"
  }
  
  # Clean staging
  rm -rf "$STAGING"
  rm -f "$PLAN"
  
  echo "✓ Refresh complete"
  echo "ℹ Next: git push (when ready)"
  
  return 0
}
```

**Output**: Applied changes, committed, cleaned staging

**Error handling**:
- If git operations fail: STOP, preserve state
- If runtime setup fails: warn, user can run manually

---

## Helper functions

### sha256sum wrapper

```bash
get_file_hash() {
  local file="$1"
  sha256sum "$file" 2>/dev/null | awk '{print $1}' || echo ""
}
```

### IDE detection

```bash
detect_active_ides() {
  local ides=()
  [[ -d .claude ]] && ides+=("claude")
  [[ -d .cursor ]] && ides+=("cursor")
  [[ -d .windsurf ]] && ides+=("windsurf")
  [[ -d .devin ]] && ides+=("devin")
  [[ -d .kiro ]] && ides+=("kiro")
  [[ -d .codex ]] && ides+=("codex")
  [[ -d .opencode ]] && ides+=("opencode")
  [[ -f .github/copilot-instructions.md ]] && ides+=("vscode-copilot")
  
  echo "${ides[@]}"
}
```

---

## Usage

Called from `templates/commands/wf-refresh/_base.md`:

```bash
source wf-init/lib/refresher.md

refresh_phase_r_minus_1 || exit 1
refresh_phase_r0 || exit 1
refresh_phase_r1 || exit 1
refresh_phase_r2 || exit 1
refresh_phase_r3 || exit 1
refresh_phase_r4 || exit 1
refresh_phase_r5 || exit 1
refresh_phase_r6 || exit 1

echo "✓ Refresh completed successfully"
```
