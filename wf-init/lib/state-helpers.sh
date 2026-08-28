#!/bin/bash
# Read/write helpers for `.wizard-state.json`.
# This file is pure bash and can be sourced by phase files and sub-agents.
# The state contract is documented in `wf-init/lib/state.md`.

WF_STATE="${WF_STATE:-.wizard-state.json}"
WIZARD_REPO="${WIZARD_REPO:-hugoafj/ai-workflow-wizard}"
WIZARD_BRANCH="${WIZARD_BRANCH:-main}"
WF_RAW="${WF_RAW:-https://raw.githubusercontent.com/${WIZARD_REPO}/${WIZARD_BRANCH}}"

# Export functions so they're available in subshells (fixes #3, #4)
export -f wf_state_get 2>/dev/null || true
export -f wf_state_set 2>/dev/null || true
export -f wf_state_validate 2>/dev/null || true
export -f wf_phase_done 2>/dev/null || true
export -f wf_sha256 2>/dev/null || true

# Ensure PATH includes Homebrew locations for macOS subshells (fixes #4)
export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH}"

# Get wizard version. Single source of truth: the wizard repo's VERSION file
# (no 'v' prefix). Falls back to a local VERSION file, then GitHub
# releases/latest and tags. Always normalizes away a leading 'v'.
wf_fetch_version() {
  local version
  # 1. VERSION file in the wizard repo (raw.githubusercontent)
  version=$(curl -fsSL "${WF_RAW}/VERSION" 2>/dev/null | head -1) || true

  # 2. Local VERSION file (e.g. offline/dev checkout)
  if [ -z "$version" ] && [ -f VERSION ]; then
    version=$(head -1 VERSION)
  fi

  # 3. Latest GitHub release (tag name may include a 'v' prefix)
  if [ -z "$version" ]; then
    version=$(curl -fsSL "https://api.github.com/repos/${WIZARD_REPO}/releases/latest" 2>/dev/null | jq -r '.tag_name // empty' 2>/dev/null) || true
  fi

  # 4. Latest tag as final remote fallback
  if [ -z "$version" ]; then
    version=$(curl -fsSL "https://api.github.com/repos/${WIZARD_REPO}/tags?per_page=1" 2>/dev/null | jq -r '.[0].name // empty' 2>/dev/null) || true
  fi

  # Final fallback
  # Strip a leading 'v' AFTER the emptiness check: VERSION="v" alone would
  # otherwise pass the -n check and echo an empty string.
  version="${version#v}"
  [ -n "$version" ] && echo "$version" || echo "0.7.1-beta.1"
}

# Initialize state if it doesn't exist (phase0 creates it on first run)
wf_state_init() {
  [ -f "$WF_STATE" ] && return 0
  local version
  version=$(wf_fetch_version)
  cat > "$WF_STATE" <<JSON
{ "schema_version": 3, "wizard_version": "$version", "phase_pointer": "phase0", "started_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")", "updated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "phases": {},
  "wf_dir": "/tmp/wf-init-phases",
  "gentle_ai": {
    "installed": null,
    "version": null,
    "install_choice": null,
    "doctor": null,
    "os": null,
    "warning_incomplete": false
  },
  "discovery": {
    "stack": { "primary": null, "framework": null, "detected_from": null, "stack_key": null },
    "node_engine": null,
    "npm_major": null,
    "default_branch": null,
    "commands": null,
    "code_files": null,
    "git_commits": null,
    "committers": null,
    "ci_present": null,
    "prior_artifacts": { "agents_md": false, "claude_md": false, "satellites": [], "hook": false },
    "classification": null,
    "conventions": {}
  },
  "answers": {
    "project_name": null,
    "stack_versions": null,
    "ides": [],
    "critical_constraints": []
  },
  "features": {
    "decision_ladder": null,
    "tdd_protocol": null,
    "routing_abc": null,
    "ci": null,
    "cd": null,
    "release_please": null
  },
  "agents": [],
  "sdd": {
    "backend": null,
    "already_initialized": false,
    "refresh_requested": null
  },
  "testing": {
    "runner_detected": null,
    "layers": [],
    "tdd_mode": null,
    "coverage_threshold": null,
    "visual_regression": false,
    "page_object_model": false
  },
  "mcps": [],
  "ci": {
    "ai_reviewer": null,
    "gga_provider": null,
    "gga_modes": [],
    "security_review": null,
    "conventional_commits": null,
    "release_please": null,
    "release_ai_summary": null,
    "release_ai_provider": null,
    "github_remote": null,
    "e2e_in_ci": false,
    "auto_improve": true,
    "inline_suggestions": true
  },
  "cd": {
    "enabled": null,
    "platform": null,
    "trigger": null,
    "vps_runtime": null,
    "stack_detected": null,
    "deploy_path": null,
    "compose_file": null,
    "missing_secrets": []
  },
  "migration": {
    "prior_content_action": null,
    "missing_commands": [],
    "wrap_custom_in_markers": false
  },
  "build_plan": {
    "agents_md": false,
    "satellites": [],
    "commands": [],
    "protocols_flat": [],
    "protocols_skills": [],
    "hook": false,
    "staging_dir": ".wizard-staging",
    "generated_files": [],
    "managed_paths": [],
    "approval": {}
  }
}
JSON
}

# Read a field (e.g. wf_state_get '.answers.project_name')
wf_state_get() { jq -r "$1 // empty" "$WF_STATE" 2>/dev/null; }

# Write a field (e.g. wf_state_set '.discovery.classification' '"legacy"')
# Returns 0 on success, 1 on failure. Verifies the write by reading back the path.
# Fixed: properly handles boolean `false` values (fixes #2)
wf_state_set() {
  local filter="$1" value="$2" tmp verify
  tmp="$(mktemp)"
  if jq "$filter = $value | .updated_at = (now | todate)" "$WF_STATE" > "$tmp"; then
    mv "$tmp" "$WF_STATE"
    # Verify write: read back the path
    verify=$(jq -r "$filter // empty" "$WF_STATE" 2>/dev/null)
    # Handle boolean false explicitly - jq returns literal 'false' not empty string
    if [ -z "$verify" ] && [ "$value" != "null" ] && [ "$value" != '""' ] && [ "$value" != "false" ]; then
      echo "ERROR: wf_state_set wrote but verification failed for $filter" >&2
      return 1
    fi
    # Additional check: if value was "false", verify it reads back as "false"
    if [ "$value" = "false" ] && [ "$verify" != "false" ]; then
      echo "ERROR: wf_state_set wrote false but verification returned '$verify' for $filter" >&2
      return 1
    fi
  else
    rm -f "$tmp"
    echo "ERROR: wf_state_set jq failed for $filter" >&2
    return 1
  fi
}

# Validate critical state fields before phase transition
# Returns 0 if valid, 1 if corrupted
# Phase-aware validation (fixes #1, #10): accepts optional phase name to validate only
# fields that should exist by that phase. If no phase given, validates all required fields.
wf_state_validate() {
  local phase="${1:-all}"
  local required_fields=()
  local valid=true

  case "$phase" in
    phase0b)
      # Phase 0b writes: gentle_ai.doctor, gentle_ai.version, gentle_ai.install_choice, answers.ides
      required_fields=(
        ".gentle_ai.doctor"
        ".gentle_ai.version"
        ".answers.ides"
      )
      ;;
    phase0c)
      # Phase 0c writes: all 6 features
      required_fields=(
        ".features.decision_ladder"
        ".features.tdd_protocol"
        ".features.routing_abc"
        ".features.ci"
        ".features.cd"
        ".features.release_please"
      )
      ;;
    phase1)
      # Phase 1 writes: discovery.stack.primary, discovery.classification
      required_fields=(
        ".discovery.stack.primary"
        ".discovery.classification"
      )
      ;;
    phase2)
      # Phase 2 writes: migration.prior_content_action
      required_fields=(
        ".migration.prior_content_action"
      )
      ;;
    phase45)
      # Phase 4.5 writes: sdd.backend, sdd.already_initialized
      required_fields=(
        ".sdd.backend"
        ".sdd.already_initialized"
      )
      ;;
    phase46)
      # Phase 4.6 writes: testing.layers, testing.tdd_mode, testing.runner_detected
      required_fields=(
        ".testing.layers"
        ".testing.tdd_mode"
      )
      ;;
    phase46b)
      # Phase 4.6b writes: testing.coverage_threshold, testing.visual_regression, testing.page_object_model, mcps
      required_fields=(
        ".testing.visual_regression"
        ".testing.page_object_model"
      )
      # coverage_threshold can be null if not activated - check field exists not value
      ;;
    phase47-cicd)
      # Phase 4.7 writes: ci.*, cd.*
      required_fields=(
        ".ci.ai_reviewer"
        ".ci.conventional_commits"
        ".cd.enabled"
        ".cd.platform"
      )
      ;;
    phase5)
      # Phase 5 writes: answers.project_name
      required_fields=(
        ".answers.project_name"
      )
      ;;
    phase6a-agents|phase6b-build-heavy)
      # Builder phases write: build_plan.generated_files, build_plan.managed_paths
      required_fields=(
        ".build_plan.generated_files"
        ".build_plan.managed_paths"
      )
      ;;
    phase7)
      # Phase 7 validates build_plan before transition to phase8
      required_fields=(
        ".build_plan.generated_files"
        ".build_plan.managed_paths"
      )
      ;;
    phase8)
      # Phase 8 validates build_plan before final transition
      required_fields=(
        ".build_plan.generated_files"
        ".build_plan.managed_paths"
      )
      ;;
    all|*)
      # Full validation - all critical fields
      required_fields=(
        ".answers.ides"
        ".features.decision_ladder"
        ".features.tdd_protocol"
        ".features.routing_abc"
        ".features.ci"
        ".features.cd"
        ".features.release_please"
        ".discovery.stack.primary"
        ".discovery.stack.framework"
      )
      ;;
  esac

  local field
  for field in "${required_fields[@]}"; do
    if ! jq -e "$field != null" "$WF_STATE" >/dev/null 2>&1; then
      echo "ERROR: wf_state_validate - missing or null field: $field" >&2
      valid=false
    fi
  done

  # answers.ides must be array (can be empty but must exist)
  if ! jq -e '.answers.ides | type == "array"' "$WF_STATE" >/dev/null 2>&1; then
    echo "ERROR: wf_state_validate - answers.ides is not an array" >&2
    valid=false
  fi

  # For phase46b, coverage_threshold is optional (can be null if coverage not activated)
  if [ "$phase" = "phase46b" ]; then
    if ! jq -e 'has("testing") and .testing | has("coverage_threshold")' "$WF_STATE" >/dev/null 2>&1; then
      echo "ERROR: wf_state_validate - testing.coverage_threshold field missing" >&2
      valid=false
    fi
  fi

  $valid
}

# Mark phase and advance pointer (e.g. wf_phase_done phase1 phase2)
# Validates state before advancing pointer (fixes #9: logs phase transition)
wf_phase_done() {
  local done_phase="$1" next="$2" tmp
  # Validate state before transition - use phase-aware validation for the phase being COMPLETED
  echo "Validating state for $done_phase → $next" >&2
  if ! wf_state_validate "$done_phase"; then
    echo "ERROR: wf_phase_done - state validation failed for $done_phase, not advancing pointer" >&2
    return 1
  fi
  tmp="$(mktemp)"
  if jq ".phases[\"$done_phase\"].status = \"done\" | .phase_pointer = \"$next\" | .updated_at = (now | todate)" \
     "$WF_STATE" > "$tmp" && mv "$tmp" "$WF_STATE"; then
    # Verify pointer advanced
    local ptr
    ptr=$(jq -r '.phase_pointer // empty' "$WF_STATE" 2>/dev/null)
    if [ "$ptr" != "$next" ]; then
      echo "ERROR: wf_phase_done - pointer not advanced to $next (got $ptr)" >&2
      return 1
    fi
  else
    return 1
  fi
}

# Compute SHA256 hash of a file with portable fallback (macOS/BSD).
# Exported for subshell use (fixes #3)
wf_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -- "$1" | awk '{print $1}'
  else
    shasum -a 256 -- "$1" | awk '{print $1}'
  fi
}

# Find local openspec-convention.md schema file (installed by gentle-ai sync)
# Searches in IDE-specific and universal locations
_find_openspec_schema() {
  local IDES="$1"
  local schema_paths=()
  
  # Universal (wizard installs here) - highest priority
  schema_paths+=("$HOME/.agents/skills/_shared/openspec-convention.md")
  
  # IDE-specific (gentle-ai sync installs here)
  case "$IDES" in
    *opencode*)  schema_paths+=("$HOME/.config/opencode/skills/_shared/openspec-convention.md") ;;
    *claude*)    schema_paths+=("$HOME/.claude/skills/_shared/openspec-convention.md") ;;
    *cursor*)    schema_paths+=("$HOME/.cursor/skills/_shared/openspec-convention.md") ;;
    *windsurf*)  schema_paths+=("$HOME/.codeium/windsurf/skills/_shared/openspec-convention.md") ;;
    *devin*)     schema_paths+=("$HOME/.devin/skills/_shared/openspec-convention.md") ;;
    *kiro*)      schema_paths+=("$HOME/.kiro/skills/_shared/openspec-convention.md") ;;
    *codex*)     schema_paths+=("$HOME/.codex/skills/_shared/openspec-convention.md") ;;
    *gemini*)    schema_paths+=("$HOME/.gemini/skills/_shared/openspec-convention.md") ;;
    *antigravity*) schema_paths+=("$HOME/.gemini/antigravity/skills/_shared/openspec-convention.md") ;;
  esac
  
  # Find first existing
  for path in "${schema_paths[@]}"; do
    if [ -f "$path" ]; then
      echo "$path"
      return 0
    fi
  done
  return 1
}

# Validate openspec/config.yaml structure against canonical schema
# Returns 0 if valid, 1 if issues found (issues printed to stderr)
# Only validates structure (keys + types), not values
validate_openspec_structure() {
  local config_file="${1:-.wizard-state.json}"  # not used, kept for API compatibility
  local IDES="${2:-$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)}"
  
  local schema_file
  schema_file=$(_find_openspec_schema "$IDES")
  
  if [ -z "$schema_file" ]; then
    echo "WARN: No local openspec-convention.md schema found (searched ~/.agents/skills/_shared/ and IDE-specific paths). Skipping validation." >&2
    return 0
  fi
  
  if [ ! -f openspec/config.yaml ]; then
    echo "ERROR: openspec/config.yaml not found" >&2
    return 1
  fi
  
  echo "=== Validating openspec/config.yaml against local schema: $schema_file ===" >&2
  
  local ISSUES=()
  
  # Check 1: Required keys from canonical schema
  local required_keys=(
    "rules.apply"
    "rules.verify"
    "testing.runner"
    "testing.layers"
    "testing.coverage"
    "testing.quality"
  )
  
  for key in "${required_keys[@]}"; do
    if ! yq eval ".$key" openspec/config.yaml | grep -qv '^null$'; then
      ISSUES+=("Missing canonical key: $key")
    fi
  done
  
  # Check 2: phase_rules legacy (common sdd-init LLM bug)
  if yq eval '.phase_rules' openspec/config.yaml | grep -qv '^null$'; then
    ISSUES+=("Legacy 'phase_rules' found (sdd-init bug). Canonical schema uses 'rules'.")
  fi
  
  # Check 3: Correct types (maps, not scalars)
  local map_keys=(
    "rules.apply"
    "rules.verify"
    "testing.runner"
    "testing.coverage"
  )
  
  for key in "${map_keys[@]}"; do
    local TYPE
    TYPE=$(yq eval ".$key | type" openspec/config.yaml 2>/dev/null)
    if [ "$TYPE" != "!!map" ] && [ "$TYPE" != "!!null" ]; then
      ISSUES+=("$key: type $TYPE (should be map, not scalar)")
    fi
  done
  
  # Check 4: testing.layers has unit/integration/e2e
  for layer in unit integration e2e; do
    if ! yq eval ".testing.layers.$layer" openspec/config.yaml | grep -qv '^null$'; then
      ISSUES+=("Missing testing.layers.$layer")
    fi
  done
  
  # Report issues
  if [ ${#ISSUES[@]} -gt 0 ]; then
    echo "ISSUES_FOUND:" >&2
    for issue in "${ISSUES[@]}"; do
      echo "  - $issue" >&2
    done
    return 1
  fi
  
  echo "✓ openspec/config.yaml structure matches canonical schema" >&2
  return 0
}

# Auto-fix common openspec/config.yaml structural issues
# Returns 0 on success, 1 on failure
fix_openspec_structure() {
  local IDES="${1:-$(jq -r '.answers.ides[]?' .wizard-state.json 2>/dev/null)}"
  
  if [ ! -f openspec/config.yaml ]; then
    echo "ERROR: openspec/config.yaml not found" >&2
    return 1
  fi
  
  echo "Applying structural fixes to openspec/config.yaml..." >&2
  
  # Fix 1: Remove legacy phase_rules
  if yq eval '.phase_rules' openspec/config.yaml | grep -qv '^null$'; then
    echo "  - Removing legacy 'phase_rules'" >&2
    yq eval 'del(.phase_rules)' -i openspec/config.yaml
  fi
  
  # Fix 2: Ensure canonical keys exist (scalar-in-path guard in phase8 will normalize types)
  # These will be created when phase8 writes rules.* and testing.*
  # No action needed here - yq creates parent maps automatically
  
  echo "✓ Structural fixes applied" >&2
  return 0
}

# Export new functions for subshell use
export -f _find_openspec_schema 2>/dev/null || true
export -f validate_openspec_structure 2>/dev/null || true
export -f fix_openspec_structure 2>/dev/null || true