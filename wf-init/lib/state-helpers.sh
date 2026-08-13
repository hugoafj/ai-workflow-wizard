#!/bin/bash
# Read/write helpers for `.wizard-state.json`.
# This file is pure bash and can be sourced by phase files and sub-agents.
# The state contract is documented in `wf-init/lib/state.md`.

WF_STATE="${WF_STATE:-.wizard-state.json}"
WIZARD_REPO="${WIZARD_REPO:-hugoafj/ai-workflow-wizard}"
WIZARD_BRANCH="${WIZARD_BRANCH:-main}"
WF_RAW="${WF_RAW:-https://raw.githubusercontent.com/${WIZARD_REPO}/${WIZARD_BRANCH}}"

# Get wizard version from the repo's VERSION file
wf_fetch_version() {
  # Try to get the latest tag from GitHub API
  local version
  version=$(curl -fsSL "https://api.github.com/repos/${WIZARD_REPO}/releases/latest" 2>/dev/null | jq -r '.tag_name // empty' 2>/dev/null)

  # If no release found, try the latest tag
  if [ -z "$version" ]; then
    version=$(curl -fsSL "https://api.github.com/repos/${WIZARD_REPO}/tags?per_page=1" 2>/dev/null | jq -r '.[0].name // empty' 2>/dev/null)
  fi

  # If still no version, fall back to VERSION file
  if [ -z "$version" ]; then
    version=$(curl -fsSL "${WF_RAW}/VERSION" 2>/dev/null | head -1)
  fi

  # Final fallback
  [ -n "$version" ] && echo "$version" || echo "v0.1.0-beta.1"
}

# Initialize state if it doesn't exist (phase0 creates it on first run)
wf_state_init() {
  [ -f "$WF_STATE" ] && return 0
  local version
  version=$(wf_fetch_version)
  cat > "$WF_STATE" <<JSON
{ "schema_version": 3, "wizard_version": "$version", "phase_pointer": "phase0",
  "phases": {}, "gentle_ai": {}, "discovery": {}, "answers": {}, "features": {},
  "agents": [], "sdd": {}, "testing": {}, "mcps": [], "migration": {}, "build_plan": {} }
JSON
}

# Read a field (e.g. wf_state_get '.answers.project_name')
wf_state_get() { jq -r "$1 // empty" "$WF_STATE" 2>/dev/null; }

# Write a field (e.g. wf_state_set '.discovery.classification' '"legacy"')
wf_state_set() {
  local filter="$1" value="$2" tmp
  tmp="$(mktemp)"
  jq "$filter = $value | .updated_at = (now | todate)" "$WF_STATE" > "$tmp" && mv "$tmp" "$WF_STATE"
}

# Mark phase and advance pointer (e.g. wf_phase_done phase1 phase2)
wf_phase_done() {
  local done_phase="$1" next="$2" tmp
  tmp="$(mktemp)"
  jq ".phases[\"$done_phase\"].status = \"done\" | .phase_pointer = \"$next\" | .updated_at = (now | todate)" \
    "$WF_STATE" > "$tmp" && mv "$tmp" "$WF_STATE"
}
