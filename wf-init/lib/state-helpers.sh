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
export -f wf_state_sanitize 2>/dev/null || true

# Ensure PATH includes Homebrew locations for macOS subshells (fixes #4)
# Idempotent prepend: only add if not already present (avoids PATH pollution in persistent shells)
case ":${PATH}:" in
  *":/opt/homebrew/bin:"*) ;;
  *) export PATH="/opt/homebrew/bin:${PATH}" ;;
esac
case ":${PATH}:" in
  *":/usr/local/bin:"*) ;;
  *) export PATH="/usr/local/bin:${PATH}" ;;
esac

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
{ "schema_version": 4, "wizard_version": "$version", "phase_pointer": "phase0", "started_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")", "updated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
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
    "stack": { "primary": null, "framework": null, "detected_from": null, "stack_key": null, "frontend": null },
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
    "decision_ladder": false,
    "testing": false,
    "ci": false,
    "cd": false,
    "release_please": false
  },
  "agents": [],
  "testing": {
    "runner_detected": null,
    "profile": null,
    "runner": null,
    "runner_existing": null,
    "environment": null,
    "test_pattern": null,
    "test_command": null,
    "frontend_profile": null,
    "frontend_runner": null,
    "frontend_runner_existing": null,
    "frontend_root": null,
    "layers": [],
    "coverage_threshold": null,
    "coverage_mode": null,
    "coverage_autoupdate": false,
    "frontend_coverage_threshold": null,
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

# Detect the Node framework from a package.json (single source of truth, shared by
# phase 1 discovery and /wf-refresh R1). Prints one token; first dependency match wins.
# Package NAMES are matched (dependencies + devDependencies), never version values.
# Order matters: nuxt before vue, next before react, nest/angular before the rest.
#   nest | angular | next | nuxt | vue | react | express | fastify | hono | koa | generic
# Prints nothing and returns 1 when the manifest is missing or is not valid JSON.
wf_detect_framework() {
  local pkg="${1:-package.json}"
  [ -f "$pkg" ] || return 1
  jq -r '
    ((.dependencies // {}) + (.devDependencies // {})) as $d
    | if   $d["@nestjs/core"]  then "nest"
      elif $d["@angular/core"] then "angular"
      elif $d["next"]          then "next"
      elif $d["nuxt"]          then "nuxt"
      elif $d["vue"]           then "vue"
      elif $d["react"]         then "react"
      elif $d["express"]       then "express"
      elif $d["fastify"]       then "fastify"
      elif $d["hono"]          then "hono"
      elif $d["koa"]           then "koa"
      else "generic" end' "$pkg" 2>/dev/null
}

# Detect the PHP framework from a composer.json (shared by phase 1 discovery and /wf-refresh R1,
# through wf_detect_stack). Prints one token: laravel | generic. Package NAMES are matched
# (require + require-dev), never version values. Prints nothing and returns 1 when the manifest
# is missing, is not valid JSON, or jq is not installed.
wf_detect_php_framework() {
  local pkg="${1:-composer.json}"
  [ -f "$pkg" ] || return 1
  jq -r '
    ((.require // {}) + (."require-dev" // {})) as $d
    | if $d["laravel/framework"] then "laravel" else "generic" end' "$pkg" 2>/dev/null || return 1
}

# Detect the project stack from the manifests in <dir> (single source of truth for phase 1
# discovery and /wf-refresh R1). Prints "<stack_key> <framework>" on one line, both tokens
# without spaces. A Laravel composer.json wins over package.json, because a Laravel app ships a
# package.json for its assets and that must not turn it into a Node project. Everything else
# keeps the previous precedence: package.json, then composer.json, then pyproject.toml.
#   php-laravel laravel | node-<framework> <framework> | php-generic generic | python-django django
#   unknown (no manifest: stack_key "unknown", framework empty)
wf_detect_stack() {
  local dir="${1:-.}" fw
  if [ -f "$dir/composer.json" ] && [ "$(wf_detect_php_framework "$dir/composer.json" 2>/dev/null)" = "laravel" ]; then
    echo "php-laravel laravel"; return 0
  fi
  if [ -f "$dir/package.json" ]; then
    fw=$(wf_detect_framework "$dir/package.json" 2>/dev/null || true)
    fw="${fw:-generic}"
    echo "node-$fw $fw"; return 0
  fi
  if [ -f "$dir/composer.json" ]; then echo "php-generic generic"; return 0; fi
  if [ -f "$dir/pyproject.toml" ]; then echo "python-django django"; return 0; fi
  echo "unknown"
}

# Folder that holds the JavaScript sources of a PHP project's frontend, relative to <dir>: the first
# of resources/js, resources/assets/js, resources/ts, resources/assets/ts that exists (Laravel's
# standard place first, then the older resources/assets layout). Prints nothing when none exists, so
# the caller asks the developer once and stores the answer in testing.frontend_root.
wf_detect_frontend_root() {
  local dir="${1:-.}" c
  for c in resources/js resources/assets/js resources/ts resources/assets/ts; do
    if [ -d "$dir/$c" ]; then echo "$c"; return 0; fi
  done
  return 0
}

# Detect the UI framework of a PHP project's frontend from its package.json (phase 1 discovery and
# /wf-refresh R1, for a php- stack). Prints react | next | vue | nuxt | angular, or none. The same
# dependency order as wf_detect_framework, except when BOTH react and vue are dependencies (a
# project that migrated, or keeps a few components of the old one): then the framework that more
# source files import wins, and the dependency order only breaks a tie. Package presence alone is
# never enough: the Laravel skeleton ships a package.json with Vite and axios and no UI framework.
wf_detect_frontend() {
  local dir="${1:-.}" pkg="${1:-.}/package.json" fw root react vue
  [ -f "$pkg" ] || { echo none; return 0; }
  fw=$(wf_detect_framework "$pkg" 2>/dev/null) || { echo none; return 0; }
  case "$fw" in
    angular|next|nuxt) echo "$fw"; return 0 ;;
    vue|react) ;;
    *) echo none; return 0 ;;
  esac
  if jq -e '((.dependencies // {}) + (.devDependencies // {})) | (.react and .vue)' "$pkg" >/dev/null 2>&1; then
    root=$(wf_detect_frontend_root "$dir"); root="$dir/${root:-.}"
    react=$(grep -rIlE --include='*.js' --include='*.jsx' --include='*.ts' --include='*.tsx' \
              --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=.git \
              -e "from ['\"]react['\"]" -e "require\(['\"]react['\"]\)" "$root" 2>/dev/null | wc -l | tr -d ' ')
    # .vue files are counted once, below, by existing: grepping them too would count a .vue file that
    # imports vue twice and tilt the tie towards vue.
    vue=$(grep -rIlE --include='*.js' --include='*.ts' \
            --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=.git \
            -e "from ['\"]vue['\"]" -e "require\(['\"]vue['\"]\)" "$root" 2>/dev/null | wc -l | tr -d ' ')
    vue=$((vue + $(find "$root" -name node_modules -prune -o -name vendor -prune -o -name '*.vue' -print 2>/dev/null | wc -l | tr -d ' ')))
    if [ "$react" -gt "$vue" ]; then fw=react; elif [ "$vue" -gt "$react" ]; then fw=vue; fi
  fi
  echo "$fw"
}

# Map a framework token (wf_detect_framework / wf_detect_stack output) to its testing profile.
# The profile selects runner, environment, packages and config template (phase 4.6, Builder B8).
#   react -> react   next -> next   vue|nuxt -> vue   express|fastify|hono|koa -> node-api
#   nest -> nest          angular -> angular          laravel -> laravel
#   anything else -> generic (a Node project) or php (a PHP project)
# "generic" is a framework token of both ecosystems, so pass the stack key's ecosystem as $2
# (the part before the first "-" of stack_key: node | php). Without it the answer is the Node one.
wf_profile_for_framework() {
  case "$1" in
    react)                        echo "react" ;;
    next)                         echo "next" ;;
    vue|nuxt)                     echo "vue" ;;
    express|fastify|hono|koa)     echo "node-api" ;;
    nest)                         echo "nest" ;;
    angular)                      echo "angular" ;;
    laravel)                      echo "laravel" ;;
    *)                            if [ "${2:-}" = "php" ]; then echo "php"; else echo "generic"; fi ;;
  esac
}

# Print the testing profile data (JSON) from templates/protocols/testing/profiles.md, the
# single source for what each profile installs, generates and documents (phase 4.6, phase 8,
# the Builder). WF_PROFILES_FILE overrides the source with a local copy of that markdown file.
wf_testing_profiles() {
  local src
  if [ -n "${WF_PROFILES_FILE:-}" ] && [ -f "$WF_PROFILES_FILE" ]; then
    src=$(cat "$WF_PROFILES_FILE")
  else
    src=$(curl -fsSL "$WF_RAW/templates/protocols/testing/profiles.md" 2>/dev/null) || return 1
  fi
  printf '%s\n' "$src" | awk '/^```json[[:space:]]*$/{f=1;next} /^```[[:space:]]*$/{f=0} f'
}

# JSON of one profile; an empty or unknown name resolves to the data file's default (react).
wf_testing_profile() {
  local data name="${1:-}"
  data=$(wf_testing_profiles) && [ -n "$data" ] \
    || { echo "wf_testing_profile: cannot read templates/protocols/testing/profiles.md from $WF_RAW" >&2; return 1; }
  printf '%s\n' "$data" | jq -e . >/dev/null 2>&1 \
    || { echo "wf_testing_profile: the profile data read from $WF_RAW is not valid JSON" >&2; return 1; }
  # Like the Builder, say so when a (typo'd) profile name falls back to the default one.
  if [ -n "$name" ] && [ "$(printf '%s\n' "$data" | jq -r --arg p "$name" '.profiles | has($p)')" != "true" ]; then
    echo "wf_testing_profile: unknown testing profile '$name', using the default profile" >&2
  fi
  printf '%s\n' "$data" | jq -c --arg p "$name" '.profiles[$p] // .profiles[.default]'
}

# Target file of the unit config the Builder writes for <profile> + <runner> (the runner only
# matters for profiles that pick a config by runner, i.e. generic). Prints nothing when the
# Builder writes none (angular, generic without Vitest). A third argument "frontend" asks for the
# config of the frontend layer of a PHP project (the profile's unit_config_frontend) instead.
wf_unit_config_target() {
  local data
  data=$(wf_testing_profiles) && [ -n "$data" ] \
    || { echo "wf_unit_config_target: cannot read templates/protocols/testing/profiles.md from $WF_RAW" >&2; return 1; }
  printf '%s\n' "$data" | jq -r --arg p "${1:-}" --arg r "${2:-}" --arg f "${3:-}" '
    (.profiles[$p] // .profiles[.default]) as $pr
    | (if $f == "frontend" then $pr.unit_config_frontend else ($pr.unit_config // $pr.unit_config_by_runner[$r]) end) as $k
    | if $k then .unit_configs[$k].target else empty end'
}

# True when <dir> holds a file whose name matches <glob>. Uses find, not a shell glob: zsh (the
# default macOS shell) aborts a command whose glob matches nothing and prints an error.
_wf_has_file() { [ -n "$(find "$1" -maxdepth 1 -type f -name "$2" 2>/dev/null | head -n 1)" ]; }

# Detect an already-configured unit test runner: its dependency AND its config, never one
# alone (a dependency without config is a broken layer, not a configured one).
# Prints vitest | jest | mocha | karma | native (an Angular CLI "test" target), or nothing.
wf_detect_runner() {
  local pkg="${1:-package.json}" deps dir
  [ -f "$pkg" ] || return 0
  dir=$(dirname "$pkg")
  deps=$(jq -r '((.dependencies // {}) + (.devDependencies // {})) | keys[]' "$pkg" 2>/dev/null) || return 0
  if printf '%s\n' "$deps" | grep -qx vitest \
     && { _wf_has_file "$dir" 'vitest.config.*' \
          || find "$dir" -maxdepth 1 -type f -name 'vite.config.*' -exec grep -lE '^[[:space:]]*test[[:space:]]*:' {} + 2>/dev/null | grep -q .; }; then
    echo vitest; return 0
  fi
  if printf '%s\n' "$deps" | grep -qx jest \
     && { _wf_has_file "$dir" 'jest.config.*' || jq -e '.jest' "$pkg" >/dev/null 2>&1; }; then
    echo jest; return 0
  fi
  if printf '%s\n' "$deps" | grep -qx mocha \
     && { _wf_has_file "$dir" '.mocharc.*' || jq -e '.mocha' "$pkg" >/dev/null 2>&1; }; then
    echo mocha; return 0
  fi
  if printf '%s\n' "$deps" | grep -qx karma && _wf_has_file "$dir" 'karma.conf.*'; then
    echo karma; return 0
  fi
  if [ -f "$dir/angular.json" ] \
     && jq -e '[.projects[]? | (.architect // .targets // {}) | .test | select(. != null)] | length > 0' \
          "$dir/angular.json" >/dev/null 2>&1; then
    echo native; return 0
  fi
  return 0
}

# Detect an already-configured PHP unit test runner from a composer.json: its dependency
# (require or require-dev) AND its config next to it, never one alone (the same rule as
# wf_detect_runner). Pest wins over PHPUnit because Pest is built on top of it.
# Prints pest | phpunit, or nothing. Returns 0 even when composer.json or jq is missing.
wf_detect_php_runner() {
  local pkg="${1:-composer.json}" deps dir
  [ -f "$pkg" ] || return 0
  dir=$(dirname "$pkg")
  deps=$(jq -r '((.require // {}) + (."require-dev" // {})) | keys[]' "$pkg" 2>/dev/null) || return 0
  if printf '%s\n' "$deps" | grep -qx 'pestphp/pest' \
     && { [ -f "$dir/tests/Pest.php" ] || _wf_has_file "$dir" 'phpunit.xml*'; }; then
    echo pest; return 0
  fi
  if printf '%s\n' "$deps" | grep -qx 'phpunit/phpunit' && _wf_has_file "$dir" 'phpunit.xml*'; then
    echo phpunit; return 0
  fi
  return 0
}

# Print the commands of a PHP project, one per line, for discovery.commands (phase 1 discovery
# and /wf-refresh R1). The Builder has a Python mirror of these rules (detect_php_commands in
# builder-core.py): change both together. In this order:
#   1. every Composer script as `composer run <name>`, sorted, except the ones Composer runs by
#      itself (names starting with pre- or post-, plus init and command);
#   2. the test command when there is no `test` script: `php artisan test` when ./artisan exists,
#      else `vendor/bin/pest` or `vendor/bin/phpunit` by dependency;
#   3. `vendor/bin/pint --dirty --test` when laravel/pint is a dependency (only the files with
#      uncommitted changes: a legacy codebase is never forced to be clean, see the CI variant);
#   4. `vendor/bin/phpstan analyse` when phpstan or larastan is a dependency;
#   5. every npm script as `npm run <name>`, sorted, when a package.json with scripts exists
#      (the frontend of a Laravel app).
# Returns 1, printing nothing, when composer.json is missing or is not valid JSON.
wf_detect_php_commands() {
  local dir="${1:-.}" artisan=false
  [ -f "$dir/composer.json" ] || return 1
  [ -f "$dir/artisan" ] && artisan=true
  jq -r --argjson artisan "$artisan" '
    ((.require // {}) + (."require-dev" // {})) as $d
    | ((.scripts // {}) | keys | map(select((test("^(pre|post)-") or . == "init" or . == "command") | not)) | sort) as $s
    | ($s[] | "composer run " + .),
      (if ($s | index("test")) then empty
       elif $artisan then "php artisan test"
       elif $d["pestphp/pest"] then "vendor/bin/pest"
       elif $d["phpunit/phpunit"] then "vendor/bin/phpunit"
       else empty end),
      (if $d["laravel/pint"] then "vendor/bin/pint --dirty --test" else empty end),
      (if ($d["phpstan/phpstan"] or $d["larastan/larastan"] or $d["nunomaduro/larastan"]) then "vendor/bin/phpstan analyse" else empty end)
  ' "$dir/composer.json" 2>/dev/null || return 1
  if [ -f "$dir/package.json" ]; then
    jq -r '((.scripts // {}) | keys | sort[]) | "npm run " + .' "$dir/package.json" 2>/dev/null || true
  fi
}

# Print a notice addressed to the AGENT when the project folder is not the root of its git repository
# (git rev-parse --show-prefix is not empty), and nothing otherwise. Used at the end of /wf-init (8.5)
# and /wf-refresh (R6). The wizard assumes the project folder IS the repository root; it does not try to
# fix other layouts, it says so and offers help.
wf_git_prefix_notice() {
  local dir="${1:-.}" prefix top
  prefix=$(git -C "$dir" rev-parse --show-prefix 2>/dev/null) || return 0
  [ -n "$prefix" ] || return 0
  top=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null) || return 0
  prefix="${prefix%/}"
  cat <<NOTICE_EOF

⚠ This project is not at the root of its git repository.
  Project folder:  $top/$prefix
  Repository root: $top

The wizard assumes the project folder IS the repository root, so some of the files it generated will
not work as generated:
  - .github/workflows/*.yml: GitHub only reads workflows from $top/.github/workflows, and their steps
    run from the repository root. They need to live there and set \`working-directory: $prefix\`.
  - Anything else that expects the repository root (git hooks such as .husky or post-commit) may need
    its paths adjusted.

AGENT: tell the user that this layout is not standard for the wizard (it is a legitimate layout, it is
just not automated), list which of the files above exist in this project, and ask whether they want
your help adjusting them. Do not change anything before they answer.
NOTICE_EOF
}

# Write a field safely using jq --arg to prevent injection/escaping issues
# 
# USAGE:
#   wf_state_set '.field' "string_value"          — writes as JSON string
#   wf_state_set '.field' "true"                   — writes as JSON boolean (jq parses it)
#   wf_state_set '.field' "false"                  — writes as JSON boolean (jq parses it)
#   wf_state_set '.field' "42"                     — writes as JSON number (jq parses it)
#   wf_state_set '.field' "null"                   — writes as JSON null (jq parses it)
#
# The second argument is ALWAYS passed as a bash string to jq --arg, which:
#   1. Safely handles any string content (quotes, newlines, backslashes, etc.)
#   2. Attempts to parse it as JSON (true/false/null/numbers/arrays/objects)
#   3. Falls back to treating it as a literal string if not valid JSON
#
# Returns 0 on success, 1 on failure. Verifies the write by reading back the path.
wf_state_set() {
  local filter="$1" value="$2" tmp verify

  # discovery.conventions is consumed as an object (builder-core calls .get on it).
  # Normalize non-object values at write time (free text becomes {"code_style": ...}).
  if [ "$filter" = ".discovery.conventions" ] && \
     ! printf '%s' "$value" | jq -e 'type == "object"' >/dev/null 2>&1; then
    echo "WARNING: wf_state_set - discovery.conventions should be an object; wrapping value as code_style." >&2
    value="$(jq -nc --arg s "$value" '{code_style: $s}')"
  fi

  # build_plan.generated_files / managed_paths are iterated as lists by the builders.
  # Reject anything else (e.g. a file count) instead of corrupting the state.
  case "$filter" in
    .build_plan.generated_files|.build_plan.managed_paths)
      if ! printf '%s' "$value" | jq -e 'type == "array"' >/dev/null 2>&1; then
        echo "ERROR: wf_state_set - $filter must be a JSON array of paths; refusing to write." >&2
        return 1
      fi
      ;;
  esac

  tmp="$(mktemp)"

  # Use jq --arg to safely pass the value, preventing injection and escaping issues.
  # Use try-catch because fromjson? treats 'false' as empty (jq quirk where false is falsy).
  # try: parse as JSON, catch: if invalid JSON, use literal string (or null if $val=="null").
  if jq --arg val "$value" "$filter = (try (\$val | fromjson) catch (if \$val == \"null\" then null else \$val end)) | .updated_at = (now | todate)" "$WF_STATE" > "$tmp" 2>/dev/null; then
    mv "$tmp" "$WF_STATE"
    
    # Verify write: read back the path (without -r, without // empty)
    # jq returns: "true"/"false" for booleans, "null" for missing OR explicit null, quoted string for strings
    verify=$(jq "$filter" "$WF_STATE" 2>/dev/null)
    
    # verify is "null" if missing OR explicitly set to null, "true"/"false" for booleans, or quoted string
    # Allow explicit null as valid (caller passed "null" as value)
    if [ "$verify" = "null" ] && [ "$value" != "null" ]; then
      echo "ERROR: wf_state_set wrote but verification failed for $filter" >&2
      return 1
    fi
    
    # Additional check: if value was "false", verify it reads back as "false"
    if [ "$value" = "false" ] && [ "$verify" != "false" ]; then
      echo "ERROR: wf_state_set wrote false but verification returned '$verify' for $filter" >&2
      return 1
    fi
    
    # If value was "true", verify it reads back as "true"
    if [ "$value" = "true" ] && [ "$verify" != "true" ]; then
      echo "ERROR: wf_state_set wrote true but verification returned '$verify' for $filter" >&2
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
    phase0)
      # Phase 0 initializes: gentle_ai.*, answers.ides (empty array), features.*, discovery.* (all null)
      # Only validate that the state file exists and has basic structure
      required_fields=(
        ".gentle_ai.installed"
        ".gentle_ai.version"
        ".gentle_ai.install_choice"
        ".gentle_ai.os"
        ".answers.ides"
      )
      ;;
    phase0b)
      # Phase 0b writes: gentle_ai.doctor, gentle_ai.version, gentle_ai.install_choice, answers.ides
      required_fields=(
        ".gentle_ai.doctor"
        ".gentle_ai.version"
        ".answers.ides"
      )
      ;;
    phase0c)
      # Phase 0c writes: all features
      required_fields=(
        ".features.decision_ladder"
        ".features.testing"
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
    phase3)
      # Phase 3 writes: discovery.classification (greenfield|legacy)
      required_fields=(
        ".discovery.classification"
      )
      ;;
    phase4)
      # Phase 4 writes: discovery.conventions, discovery.test_dir
      required_fields=(
        ".discovery.conventions"
        ".discovery.test_dir"
      )
      ;;
    phase46)
      # Phase 4.6 writes: testing.layers, testing.runner_detected, testing.coverage_threshold,
      # testing.visual_regression, testing.page_object_model
      required_fields=(
        ".testing.layers"
        ".testing.visual_regression"
        ".testing.page_object_model"
      )
      # coverage_threshold is checked below (field must exist; a number when coverage is active)
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
        ".features.testing"
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

  # For phase46, coverage_threshold may be null (coverage extra not activated) but the field must exist.
  # When coverage is active it must hold a number (0 is valid for the ratchet mode).
  # coverage_mode and coverage_autoupdate may be absent in states written before ratchet existed.
  if [ "$phase" = "phase46" ]; then
    if ! jq -e '.testing | has("coverage_threshold") and (.coverage_threshold == null or (.coverage_threshold | type == "number"))' "$WF_STATE" >/dev/null 2>&1; then
      echo "ERROR: wf_state_validate - testing.coverage_threshold missing or not a number" >&2
      valid=false
    fi
    if ! jq -e '.testing | (.coverage_mode == null or (.coverage_mode | IN("full", "ratchet"))) and ((.coverage_autoupdate // false) | type == "boolean")' "$WF_STATE" >/dev/null 2>&1; then
      echo "ERROR: wf_state_validate - testing.coverage_mode must be null, full or ratchet, and coverage_autoupdate a boolean" >&2
      valid=false
    fi
    if ! jq -e '.testing | (.frontend_coverage_threshold == null or (.frontend_coverage_threshold | type == "number"))' "$WF_STATE" >/dev/null 2>&1; then
      echo "ERROR: wf_state_validate - testing.frontend_coverage_threshold must be null or a number" >&2
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

# Strip machine-specific data from the state before it is committed.
# .wizard-state.json is versioned, so it must not carry absolute or relative paths
# to the wizard install dir. Older builders recorded them in build_plan.builder_core.scripts
# (nothing reads that field). Idempotent; a no-op on clean states.
wf_state_sanitize() {
  local tmp
  tmp="$(mktemp)"
  if jq 'del(.build_plan.builder_core.scripts)' "$WF_STATE" > "$tmp" 2>/dev/null; then
    mv "$tmp" "$WF_STATE"
  else
    rm -f "$tmp"
    echo "ERROR: wf_state_sanitize failed" >&2
    return 1
  fi
}