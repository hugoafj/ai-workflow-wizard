#!/bin/bash
# Read/write helpers for `.wizard-state.json`.
# This file is pure bash and can be sourced by phase files and sub-agents.
# The state contract is documented in `wf-init/lib/state.md`.

WF_STATE="${WF_STATE:-.wizard-state.json}"
WIZARD_REPO="${WIZARD_REPO:-hugoafj/ai-workflow-wizard}"
WIZARD_BRANCH="${WIZARD_BRANCH:-main}"
WF_RAW="${WF_RAW:-https://raw.githubusercontent.com/${WIZARD_REPO}/${WIZARD_BRANCH}}"

# Get wizard version. Single source of truth: the wizard repo's VERSION file
# (no 'v' prefix). Falls back to a local VERSION file, then GitHub
# releases/latest and tags. Always normalizes away a leading 'v'.
wf_fetch_version() {
  local version
  # 1. VERSION file in the wizard repo (raw.githubusercontent)
  version=$(curl -fsSL "${WF_RAW}/VERSION" 2>/dev/null | head -1)

  # 2. Local VERSION file (e.g. offline/dev checkout)
  if [ -z "$version" ] && [ -f VERSION ]; then
    version=$(head -1 VERSION)
  fi

  # 3. Latest GitHub release (tag name may include a 'v' prefix)
  if [ -z "$version" ]; then
    version=$(curl -fsSL "https://api.github.com/repos/${WIZARD_REPO}/releases/latest" 2>/dev/null | jq -r '.tag_name // empty' 2>/dev/null)
  fi

  # 4. Latest tag as final remote fallback
  if [ -z "$version" ]; then
    version=$(curl -fsSL "https://api.github.com/repos/${WIZARD_REPO}/tags?per_page=1" 2>/dev/null | jq -r '.[0].name // empty' 2>/dev/null)
  fi

  # Final fallback
  [ -n "$version" ] && echo "${version#v}" || echo "0.7.1-beta.1"
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

# Compute SHA256 hash of a file with portable fallback (macOS/BSD).
wf_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

# Mark phase and advance pointer (e.g. wf_phase_done phase1 phase2)
wf_phase_done() {
  local done_phase="$1" next="$2" tmp
  tmp="$(mktemp)"
  jq ".phases[\"$done_phase\"].status = \"done\" | .phase_pointer = \"$next\" | .updated_at = (now | todate)" \
    "$WF_STATE" > "$tmp" && mv "$tmp" "$WF_STATE"
}
