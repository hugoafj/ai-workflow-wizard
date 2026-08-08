# /wf-refresh — Refresh Wizard

⚡ **AUTOMATION**: Phases -1 and 0 run automatically (version check + validation). Layers 1–3 are interactive (you approve changes before applying).

---

> Intelligent three-layer refresh to keep AGENTS.md
> synchronized with (a) the project state, (b) the latest wizard template
> (Layer 2 injects changes directly), and (c) optional features you decide to adopt.
> Also includes missing command verification (Phase 3.5) for projects that
> ran /wf-init on an older version before new commands were introduced.
> Source: github.com/hugoafj/ai-workflow-wizard
> Works as a complement to `/wf-init`. Assumes /wf-init already ran in this repo before.

## What this refresh does

Detects three types of drift and applies updates incrementally, without requiring
re-running `/wf-init` or cleaning the project:

- **Layer 1 · Project content drift**: the project has evolved (new scripts,
  different structure, added dependencies) and AGENTS.md is out of date.
  The refresh detects the differences and proposes the exact diff. With your OK, it writes it.
- **Layer 2 · Template drift (mandatory changes)**: the wizard has a newer
  version with rules or fixes that all projects must have. The refresh
  builds the full diff and injects it directly into the existing AGENTS.md.
  It does not ask you to do it manually — it does it itself, with your prior approval.
- **Layer 3 · New optional features**: the wizard introduced features that depend
  on your project's context and that you decide whether to adopt or not. The refresh
  proposes them one by one and waits for your decision before touching anything.

---

## How /wf-refresh works

**Automation + Human guidance:**
- **Phases -1 & 0** (automated): Execute version checks and validations automatically
- **Layers 1–3** (interactive): Analyze and propose changes; pause for user approval

**Your role as the agent:**

1. **Execute Phase -1** (version check): Extract versions, compare, block if mismatch
2. **Execute Phase 0** (validation): Check AGENTS.md, gentle-ai, SDD; stop if blockers found
3. **Analyze** project drift (Layer 1), mandatory changes (Layer 2), optional features (Layer 3)
4. **Propose changes** with clear diffs
5. **Pause** waiting for user approval before writing
6. **Apply changes** only after explicit OK

**Inviolable rules**:

1. Do NOT write changes to `AGENTS.md` or satellites without explicit user OK.
2. Do NOT `git add` or `git commit` until the final OK.
3. Show clear diffs before applying any changes.
4. Respect content marked with `<!-- WF: DO NOT REGENERATE -->`.
5. If a user response is ambiguous, ask again.

---

## Phase -1 · Global commands version check (AUTOMATED)

**This phase MUST run FIRST, before anything else.**

> **Why this phase exists**: If `/wf-refresh` detects a new version available remotely but the command itself is outdated, it will apply changes using old logic. This phase ensures atomic updates by detecting version mismatch BEFORE any other work happens.

**Execution** (you execute this automatically on skill start):

```bash
# CRITICAL: Extract REPO from AGENTS.md footer
SOURCE_URL=$(grep "source:" AGENTS.md 2>/dev/null | tail -1 | sed 's/.*source: //')
REPO=$(echo "$SOURCE_URL" | sed 's|github.com/||' || echo "hugoafj/ai-workflow-wizard")

# Get local version from AGENTS.md footer
LOCAL_VER=$(grep -oP 'wf-version: \K[v0-9a-z.-]+' AGENTS.md | tail -1)

# Get remote version from VERSION file or GitHub API
REMOTE_VER=$(curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/VERSION" 2>/dev/null | head -1)
if [ -z "$REMOTE_VER" ]; then
  REMOTE_VER=$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" 2>/dev/null | jq -r '.tag_name // empty' 2>/dev/null)
fi

# BLOCK if versions don't match
if [ -n "$REMOTE_VER" ] && [ -n "$LOCAL_VER" ] && [ "$REMOTE_VER" != "$LOCAL_VER" ]; then
  printf '\n┌────────────────────────────────────────────────────────┐\n' >&2
  printf '│  ⚠  WIZARD VERSION MISMATCH — UPGRADE REQUIRED         │\n' >&2
  printf '└────────────────────────────────────────────────────────┘\n' >&2
  printf '\n  Remote version: %s\n' "$REMOTE_VER" >&2
  printf '  Your version:   %s\n' "$LOCAL_VER" >&2
  printf '\n  The /wf-refresh command you are running is version %s.\n' "$LOCAL_VER" >&2
  printf '  To apply all updates correctly, upgrade the global commands first.\n\n' >&2
  printf '  UPGRADE REQUIRED:\n' >&2
  printf '    1. Run: curl -fsSL https://raw.githubusercontent.com/%s/main/install.sh | bash\n' "$REPO" >&2
  printf '    2. Restart your IDE completely (quit and reopen)\n' >&2
  printf '    3. Run /wf-refresh AGAIN in a NEW chat session\n\n' >&2
  printf '  Do you want to upgrade now?\n' >&2
  printf '  [Type "upgrade" to proceed, or "skip" to continue anyway]\n\n' >&2
  
  read -p "  Your choice: " upgrade_choice
  
  if [ "$upgrade_choice" = "upgrade" ]; then
    echo "Upgrading global commands from $LOCAL_VER to $REMOTE_VER..."
    curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/install.sh" | bash
    echo ""
    echo "✓ Global commands upgraded."
    echo ""
    echo "⚠ RESTART YOUR IDE AND RUN /wf-refresh AGAIN IN A NEW CHAT SESSION"
    exit 0
  fi
  
  printf '\n⚠  Continuing with version %s. Some updates may be incomplete.\n\n' "$LOCAL_VER" >&2
fi
```

---

## Phase 0 · Pre-check (AUTOMATED)

**Execution** (you execute this automatically after Phase -1 passes):

Verify we are in a project initialized by the workflow:

```bash
# AGENTS.md must exist
ls AGENTS.md

# Must have footer with wf-version
grep "wf-version:" AGENTS.md | tail -1
```

- **If AGENTS.md does not exist**: this repo was not initialized with `/wf-init`. Stop.
  Suggest to the user: "This repo has no AGENTS.md. To initialize the workflow,
  run `/wf-init` first, not `/wf-refresh`."
- **If AGENTS.md exists but has no `wf-version` footer**: it was edited by hand or
  generated by a different tool. Stop. Suggest: "AGENTS.md exists but
  has no workflow version footer. Do you want to convert it to the workflow
  format by running `/wf-init` in migration mode?"
- **If AGENTS.md has a footer**: continue to Phase 1.

Also verify gentle-ai (same as in wf-init):

```bash
gentle-ai doctor
```

If it is `degraded` with only cosmetic warnings, OK. If it has `failed`, stop
and guide the user to fix it.

Verify that SDD is initialized in the repo (mandatory requirement):

```bash
ls openspec/config.yaml openspec/changes openspec/specs 2>/dev/null
```

If any of the three is missing, stop and ask the user:

```
The repo does not have SDD initialized (openspec/ is missing). Without this initialization,
the SDD sub-agents (sdd-propose, sdd-tasks, etc.) cannot function — any
attempt to start SDD phases will fail.

Please run /sdd-init in your IDE/CLI now. When it asks about the
persistence backend, review the options:
- engram: local memory only, no versioned files. Only if you will work
  alone indefinitely on this project.
- openspec: everything versioned in the repo. Shared with the team via git.
- hybrid: both. Recommended for most projects.

When done, tell me "done".
```

> **BLOCKING RULE (protocol `sdd`)**: Do NOT create `openspec/config.yaml`, `openspec/specs/`,
> `openspec/changes/` or any SDD artifact by hand, nor read the `SKILL.md` of sdd-init
> to replicate it, nor run `gentle-ai sdd-init` (it does not exist). If `/sdd-init` cannot be
> invoked/confirmed here, ask the user to run it in a **NEW session/chat** with
> gentle-ai skills. Creating files by hand silently corrupts SDD.

Stop the refresh until the user confirms and the verification passes.

If `openspec/config.yaml` exists, detect the backend and offer refresh if applicable:

```bash
cat openspec/config.yaml | grep -iE "backend|persistence|storage" | head -5
```

If the current backend is `engram`, check if the team has grown in the last 30 days:

```bash
# CRITICAL: use explicit `HEAD` and `< /dev/null` — without this, `git shortlog`
# can hang waiting for stdin input indefinitely instead of failing
# fast if the repo has no commits in the range, stalling the refresh without notice.
git shortlog -sne --since="30 days ago" HEAD < /dev/null 2>/dev/null | wc -l
```

If the result is more than 1 committer, suggest migration:

```
The current SDD backend is "engram" (local-only memory). I detected that there are
<N> active committers in the last 30 days. The official
gentle-ai documentation recommends migrating to "hybrid" when more developers join the project,
so that the SDD context is shared via git instead of living only in fragmented
local memories.

Run /sdd-init now to migrate to hybrid? [yes / no, keep engram]
```

If the user accepts, guide them to re-run `/sdd-init` and choose hybrid. If not, continue with the normal refresh.

---

## Phase 1 · Layer 1 — Project content drift

Re-run the wizard's reverse engineering phase against the current repo state.
Compare with the current AGENTS.md content.

Steps:

1. Read the full current AGENTS.md.
2. Re-read the project's main manifest (`package.json`, `composer.json`, etc.)
   and compare:
   - **Scripts**: Are there scripts in the manifest that are not documented in the
     `Commands` section of AGENTS.md?
   - **Stack**: Are there major new dependencies that change the Stack description?
   - **Structure**: list top-level of `src/` (or equivalent) and compare against the
     `Project Structure` section. Are there new undocumented folders, or documented
     ones that no longer exist?
3. Sample 2-3 representative files to detect convention changes (if
   it was named export before and now everything is default export, for example).

**Expected output to the user**:

```
Layer 1 · Project content drift

Drift detected:
- "Commands" section: missing the `test` and `coverage` scripts (added to package.json
  after the last initialization).
- "Project Structure" section: folder `src/services/` exists and is not documented.

No drift:
- Stack: no changes.
- Code Style: no changes.
- Critical Constraints: no changes.
- Testing: no changes.

Apply the proposed updates to this layer? [yes / no / let me see the diff]
```

**PAUSE**. Wait for user response.

- If they say "let me see the diff": show the exact diff of the proposed AGENTS.md.
- If they say "yes": save the changes to buffer (do NOT write them yet). Advance to Phase 2.
- If they say "no": mark this layer as "skipped". Advance to Phase 2.

If there is NO drift in this layer, simply report "Layer 1: no drift detected" and
advance to Phase 2 without pausing.

---

## Phase 2 · Layer 2 — Template drift (mandatory changes)

**This phase downloads ALL files from the new wizard version and regenerates any files that changed.**

### Helper: render_template function

```bash
render_template() {
  local template_content="$1"
  local state_file="$2"
  
  if [ ! -f "$state_file" ]; then
    echo "$template_content"
    return 0
  fi
  
  local output="$template_content"
  local in_if_block=0
  local condition_var=""
  local condition_value=""
  local block_content=""
  local line_num=0
  local processed=""
  
  # First pass: handle {{if var}} ... {{/if}} conditional blocks
  # Read state file once into variables for performance
  local state_json=$(cat "$state_file")
  
  while IFS= read -r line; do
    ((line_num++))
    
    if [[ "$line" =~ \{\{if\ ([a-zA-Z0-9_.]+)\}\} ]]; then
      # Start of conditional block
      condition_var="${BASH_REMATCH[1]}"
      condition_value=$(echo "$state_json" | jq -r ".${condition_var} // empty" 2>/dev/null)
      in_if_block=1
      block_content=""
    elif [[ "$line" =~ \{\{/if\}\} ]]; then
      # End of conditional block
      if [ "$in_if_block" = 1 ]; then
        # Only include block content if condition is true
        if [ -n "$condition_value" ] && [ "$condition_value" != "false" ] && [ "$condition_value" != "null" ]; then
          processed="${processed}${block_content}"
        fi
        in_if_block=0
        block_content=""
        condition_var=""
        condition_value=""
      fi
    elif [ "$in_if_block" = 1 ]; then
      block_content="${block_content}${line}"$'\n'
    else
      processed="${processed}${line}"$'\n'
    fi
  done <<< "$output"
  
  output="$processed"
  
  # Second pass: replace {{variable}} placeholders
  # Only process variables that look like state paths (contain at least one dot)
  # This avoids replacing GitHub Actions syntax like {{ steps.release.outputs.pr }}
  local max_iterations=100
  local iteration=0
  while [[ "$output" =~ \{\{([a-zA-Z0-9_.]+)\}\} ]] && [ $iteration -lt $max_iterations ]; do
    ((iteration++))
    local var_path="${BASH_REMATCH[1]}"
    
    # Only process if it looks like a state path (contains a dot)
    if [[ "$var_path" == *.* ]]; then
      local var_value=$(echo "$state_json" | jq -r ".${var_path} // empty" 2>/dev/null)
      
      if [ -z "$var_value" ]; then
        var_value="(undefined: $var_path)"
      fi
      
      # Escape special regex characters in var_value
      var_value=$(printf '%s\n' "$var_value" | sed -e 's/[\/&]/\\&/g')
      
      output=$(printf '%s\n' "$output" | sed "s/{{${var_path}}}/${var_value}/g")
    else
      # Don't process variables without dots - they're likely GitHub Actions syntax
      break
    fi
  done
  
  echo "$output"
}
```

### Download and apply WIZARD_MANIFEST.json

```bash
# Extract repo from AGENTS.md footer
SOURCE_URL=$(grep "source:" AGENTS.md | tail -1 | sed 's/.*source: //')
REPO=$(echo "$SOURCE_URL" | sed 's|github.com/||')

# Download WIZARD_MANIFEST.json from remote (from .wizard-manifests/ folder)
MANIFEST=$(curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/WIZARD_MANIFEST.json" 2>/dev/null)

if [ -z "$MANIFEST" ]; then
  echo "ERROR: Could not download WIZARD_MANIFEST.json from ${REPO}"
  exit 1
fi

REMOTE_VERSION=$(echo "$MANIFEST" | jq -r '.version')
LOCAL_VERSION=$(grep -oP 'wf-version: \K[v0-9a-z.-]+' AGENTS.md | tail -1)

echo "Wizard version check:"
echo "  Remote: $REMOTE_VERSION"
echo "  Local:  $LOCAL_VERSION"
echo ""
```

### Download and regenerate all files

```bash
# For each file in manifest
echo "$MANIFEST" | jq -r '.files | keys[]' | while read FILE_KEY; do
  FILE=$(echo "$MANIFEST" | jq -r ".files.\"$FILE_KEY\"")
  
  FILE_PATH=$(echo "$FILE" | jq -r '.path')
  OUTPUT=$(echo "$FILE" | jq -r '.output')
  REGENERATE=$(echo "$FILE" | jq -r '.regenerate')
  TEMPLATE=$(echo "$FILE" | jq -r '.template')
  STATE_VARS=$(echo "$FILE" | jq -r '.state_vars | @csv' | tr -d '"')
  STATUS=$(echo "$FILE" | jq -r '.status')
  
  echo "Downloading: $FILE_KEY ($STATUS)"
  
  # Download file from remote
  FILE_CONTENT=$(curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/${FILE_PATH}" 2>/dev/null)
  
  if [ -z "$FILE_CONTENT" ]; then
    echo "  ⚠ Could not download $FILE_PATH"
    continue
  fi
  
  # If file needs regeneration from template
  if [ "$REGENERATE" = "true" ] && [ "$TEMPLATE" != "null" ]; then
    echo "  ▶ Regenerating from template: $TEMPLATE"
    
    # Get template from remote
    TEMPLATE_CONTENT=$(curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/${TEMPLATE}" 2>/dev/null)
    
    if [ -z "$TEMPLATE_CONTENT" ]; then
      echo "  ⚠ Could not download template: $TEMPLATE"
      continue
    fi
    
    # Get state variables from .wizard-state.json
    if [ ! -f ".wizard-state.json" ]; then
      echo "  ⚠ .wizard-state.json not found, skipping regeneration"
      continue
    fi
    
    echo "    State variables:"
    for VAR in $STATE_VARS; do
      VAR_VALUE=$(jq -r ".${VAR} // \"(not set)\"" .wizard-state.json 2>/dev/null)
      echo "      ${VAR}: ${VAR_VALUE}"
    done
    
    # Regenerate file with template + state variables
    REGENERATED=$(render_template "$TEMPLATE_CONTENT" ".wizard-state.json")
    
    # Show diff if file exists
    if [ -f "$OUTPUT" ]; then
      echo "    Diff:"
      diff -u "$OUTPUT" <(echo "$REGENERATED") 2>/dev/null | head -20 || true
    fi
    
    # Create parent directory if needed
    mkdir -p "$(dirname "$OUTPUT")"
    
    # Write regenerated file
    echo "$REGENERATED" > "$OUTPUT"
    echo "  ✓ Regenerated: $OUTPUT"
  else
    # Static file, just download and write
    if [ -n "$OUTPUT" ] && [ "$OUTPUT" != "null" ]; then
      mkdir -p "$(dirname "$OUTPUT")"
      echo "$FILE_CONTENT" > "$OUTPUT"
      echo "  ✓ Written: $OUTPUT"
    fi
  fi
done
```

### Summary

All files from manifest have been downloaded and regenerated:
- ✅ Static files: downloaded and written
- ✅ Generated files: rebuilt from templates with current state
- ✅ New files: available in project
- ℹ️ New features: available in `/wf-settings` (not auto-enabled)

**Content to inject for the "wf-sdd-trigger" section**:

When AGENTS.md does not have this section in "Behavior preferences", the refresh
inserts it **immediately before the HTML comment footer** (or at the end of "Behavior
preferences" if there is no footer). The content is always the same:

> The content of the `wf-sdd-trigger` section is read from
> `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/wf-sdd-trigger/_base.md`
> (Minimal Exploration, Decision Tree, `wf-no-sdd`/`wf-force-sdd` outcomes, `wf-preflight`,
> wf-sdd-trigger evaluation fragment). Insert that content
> VERBATIM, character by character, immediately before the HTML `wf-version` footer (or at the
> end of "Behavior preferences" if there is no footer). Do not paraphrase or omit subsections.
> Also ensure `wf-orchestrator`'s content is present (it is built whenever `wf-sdd-trigger` OR
> `wf-ladder` is active — see `templates/protocols/wf-orchestrator/_base.md`).
>
> In projects with Claude Code, the same content is already packaged as skills in
> `.claude/skills/wf-sdd-trigger/SKILL.md` and `.claude/skills/wf-orchestrator/SKILL.md`; for
> other IDEs, in `.agents/protocols/wf-sdd-trigger.md` and `.agents/protocols/wf-orchestrator.md`.
> When refreshing, also regenerate those packages from the single source (Builder B4) so they do
> not get out of sync. For adapters whose orchestrator reads `.atl/skill-registry.md` before
> delegating (Claude Code, OpenCode, Cursor, Kiro, Codex), also run `gentle-ai skill-registry
> refresh` if available so gentle-ai's own Skill Resolver Protocol picks them up. **This step is a
> no-op for Windsurf/Devin** — confirmed against gentle-ai's own source
> (`internal/skillregistry/registry.go`), it never scans `.windsurf/skills/` or `.devin/skills/`
> at all; those two adapters discover project skills natively from the filesystem instead, with
> no registry step needed or possible.

**Expected output to the user** when entering Layer 2 (example):

```
Layer 2 · Template drift — mandatory changes

Your AGENTS.md is on an older wf-version. Current version: 0.1.0-beta.1.

Pending changes I will apply:

▶ AGENTS.md — add "wf-sdd-trigger" section in Behavior preferences

  Defines this project's own policy for when to explicitly request gentle-ai's
  SDD (wf-no-sdd vs wf-force-sdd) decision logic.
  Includes decision tree, criteria for each outcome, mandatory wf-preflight with
  verifiable decision logic with user confirmation.
  Never re-specifies how gentle-ai itself routes or delegates — that remains
  gentle-ai's own native authority, per adapter.

--- DIFF AGENTS.md ---
+ ### 📋 wf-sdd-trigger: when this project forces gentle-ai's SDD
+
+ > This protocol decides ONE thing: does this change meet this project's own
+ > rules for explicitly requesting gentle-ai's SDD? It never decides HOW
+ > gentle-ai then routes, delegates, or executes — that is gentle-ai's native
+ > orchestrator's exclusive authority, already installed for this adapter.
+ ...

▶ AGENTS.md — update footer: wf-version 2.1 → 3.23 + new features format

  Before: wf-version: 2.1 | ... | optional-features: decision-ladder=yes
  After: wf-version: 3.23 | ... | features: ladder=yes, tdd=no, routing=no, ci=no, cd=no, release=no

Apply these changes? [yes / no / show me the full AGENTS.md after]
```

**PAUSE**. Wait for response.

- `yes`: apply all mandatory changes to buffer. **CRITICAL: Always update footer and state:**
  
  ```bash
  # Extract remote version
  REMOTE_VERSION=$(echo "$MANIFEST" | jq -r '.version')
  
  # 1. Update AGENTS.md footer with new wf-version (ALWAYS, even if no other changes)
  sed -i "s/wf-version: [^ ]*/wf-version: $REMOTE_VERSION/" AGENTS.md
  
  # 2. Update .wizard-state.json to sync version
  if [ -f ".wizard-state.json" ]; then
    jq ".version = \"$REMOTE_VERSION\"" .wizard-state.json > /tmp/ws.json
    mv /tmp/ws.json .wizard-state.json
  fi
  ```
  
  Then advance to Layer 3.
- `no`: record that the user rejected the mandatory changes. Advance to Layer 3
  anyway (rejected mandatory changes will be proposed again on the
  next refresh). The footer is NOT updated (so the next refresh detects them).
- `show me the full AGENTS.md after`: show the full AGENTS.md with all
  changes applied, repeat the question.

**If `LOCAL_VERSION` equals `REMOTE_VERSION` and there are no pending changes**, report
"Layer 2: no mandatory changes" and advance to Phase 3 without pausing (footer is already
in sync, nothing to do).

**If `LOCAL_VERSION` differs from `REMOTE_VERSION` but none of the downloaded/compared
files produce a content change to propose in `AGENTS.md`** (e.g. the manifest only changed
metadata files like `VERSION` or internal wizard logic like a `phaseNN.md` that does not
affect this project's `AGENTS.md`): do **NOT** silently skip the footer. There is nothing
to pause for or ask approval on (no diff to show), but the footer must still reflect that
this project was checked against the new version. Silently apply the same footer/state sync
as the `yes` branch above, then report:

```
Layer 2 · Template drift — mandatory changes

No content changes required for AGENTS.md.
✓ Synced wf-version footer: <LOCAL_VERSION> → <REMOTE_VERSION>
```

Then advance to Phase 3 without pausing. **Never leave the footer pointing at a stale
version just because nothing in `AGENTS.md`'s content needed to change** — the footer
tracks "last version checked", not "last version that changed something".

---

## Phase 3 · Layer 3 — New optional features

Read the `features` field from the AGENTS.md footer. Expected format:
`features: ladder=<yes|no>, tdd=<yes|no>, routing=<yes|no>, ci=<yes|no>, cd=<yes|no>, release=<yes|no>`

If the field does NOT exist, assume the user has not seen
ANY optional feature yet, and migrate from the old format if present:
```bash
# Try to read the old format as fallback
old_features=$(grep -o "optional-features:.*" AGENTS.md 2>/dev/null | tail -1)
if [ -n "$old_features" ]; then
  echo "Migrating from legacy optional-features: $old_features"
  # Extract decision-ladder value if it exists
fi
```

Compare against the wizard's optional feature catalog. **For now** use this
hardcoded knowledge:

### Optional feature catalog

```yaml
- id: ladder
  description: |
    wf-ladder (Decision Ladder). Anti-over-engineering discipline, wizard-owned,
    no gentle-ai equivalent. The agent walks through a priority ladder before
    writing code and declares each rung out loud with its answer. Always
    applies before wf-preflight, and again per task once gentle-ai's sdd-apply
    is requested (wf-force-sdd).
  content-source: https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/wf-ladder/_base.md

- id: tdd
  description: |
    wf-tdd (TDD Protocol). RED→GREEN cycle implemented as an agent protocol.
    Includes the 🧪 TDD PROPOSAL ritual (standard mode) or direct
    RED→GREEN evidence (strict mode, via gentle-ai's strict_tdd field).
    Independent of SDD — can be injected per change without openspec/.
  content-source: https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/tdd/_base.md

- id: routing
  description: |
    wf-sdd-trigger + wf-preflight. This wizard's own policy for when
    a project's rules require explicitly requesting gentle-ai's SDD
    (wf-no-sdd vs wf-force-sdd), and mandatory wf-preflight confirmation
    before proceeding. Never re-specifies how gentle-ai itself routes or
    delegates once SDD is requested. `wf-orchestrator` (single entry point to
    this wizard's own protocols) is built alongside it.
  content-source: https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/wf-sdd-trigger/_base.md

- id: ci
  description: |
    CI (Continuous Integration). quality guard (lint+typecheck+tests),
    AI review (GGA/Claude/Gemini), security scan (Trivy/Snyk),
    conventional commits with commitlint.
  content-source: https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/

- id: cd
  description: |
    CD (Continuous Delivery). Automatic deploy to VPS (PM2, Nginx+PHP-FPM,
    Docker). Release strategy configurable (tag v* / push a main).
    Can be activated without CI.
  content-source: https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/

- id: release
  description: |
    release-please standalone. Conventional commits + release-please +
    automatic changelog and GitHub release. Optional AI summary in the
    release body. No quality guard, no AI review, no security scan —
    just the release pipeline.
  content-source: https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/cicd/variants/release-please.yml.md
```

**Logic**:

1. Iterate over each feature in the catalog.
2. For each feature:
   - If `features:` exists in the footer, look for its `id` in the `features` field (format `ladder=yes`).
   - If `features:` does NOT exist but `optional-features:` (old format) exists, look for `legacy-id` as fallback.
3. **If it does NOT appear in any field**: the feature is new for this AGENTS.md. Propose it to the user.
4. **If it appears with `=yes`**: already integrated, do not ask.
5. **If it appears with `=no`**: the user rejected it before. Do not ask again (unless
   the user passed a `--reconsider-skipped` flag).

**Expected output to the user** (if there are new features — example: `ci` is not in the footer):

```
Layer 3 · Optional features

The wizard has 2 optional features that your AGENTS.md does not include:

1. ci
   CI (Continuous Integration). quality guard (lint+typecheck+tests),
   AI review (GGA/Claude/Gemini), security scan (Trivy/Snyk),
   conventional commits with commitlint.

   Include? [yes / no / show me the full content first]

2. cd
   CD (Continuous Delivery). Automatic deploy to VPS (PM2, Nginx+PHP-FPM,
   Docker). Release strategy configurable. Can be activated without CI.

   Include? [yes / no / show me the full content first]
```

**PAUSE**. For EACH optional feature, wait for a response before moving to the next.

- `yes`: add the content to the buffer for injection into AGENTS.md. Rewrite the full
  `features:` line in the footer with the new feature as `yes`.
- `no`: rewrite the full `features:` line in the footer with that feature as `no`.
- `show me the full content first`: show the full `content-source`, repeat the question.

If there are no new optional features, report "Layer 3: your AGENTS.md is up to date
with all optional features" and advance to Phase 3.5.

---

## Phase 3.5 · Missing command verification

> **Why this phase exists**: the three previous layers (Phases 1-3) verify
> *content* drift of AGENTS.md — they do not verify whether each IDE's command
> directory has all the files that the current wizard version expects.
> A project may have run `/wf-init` on an old version (for example,
> before `wf-onboard`, `wf-refresh`, or `wf-worktree existed as
> commands), and `/wf-refresh` updates AGENTS.md correctly without ever
> noticing that those command files are missing. This phase closes that gap —
> it is the same verification that `/wf-init` does in its Step 2.1, but applied
> to a project that only runs refresh, not full init.

Derive the active IDEs from the existing satellites:

```bash
ls .claude/ .cursor/ .windsurf/ .devin/ .kiro/ .github/copilot-instructions.md .opencode/ 2>/dev/null
```

For each active IDE, verify file by file against the list of expected
commands for the current wizard version (keep in sync with
`EXPECTED_COMMANDS` from `wf-init.md`):

```bash
EXPECTED_COMMANDS="wf-ladder wf-onboard wf-refresh wf-worktree wf-settings wf-cicd wf-cleanup"

# Example for Claude Code — repeat the pattern adjusting path/extension
# for each active IDE (see route table in wf-init.md Phase 6 section)
for cmd in $EXPECTED_COMMANDS; do
  if [ ! -f ".claude/commands/${cmd}.md" ]; then
    echo "MISSING: .claude/commands/${cmd}.md"
  fi
done
```

If you find missing commands, inform the user and add them to the change
buffer (they are written together with the rest in Phase 5, not before):

```
Missing commands detected — <IDE>:
  ✗ wf-worktree.md   ← did not exist when this project ran /wf-init

Add this command now as part of the refresh? [yes / no / show content first]
```

**PAUSE**. For each missing command, wait for a response before continuing.

- `yes`: add the file to the Phase 5 write buffer, with the IDE-appropriate
  content (same format that `wf-init.md` generates in its Phase 6).
- `no`: do not add it. It will not be asked again in future refreshes unless
  the user explicitly requests it — avoids fatigue from repeating the same question.
- `show content first`: show the full content of the proposed
  command, repeat the question.

If no commands are missing in any active IDE, report "Command verification:
all active IDEs have the expected commands for this version" and advance
to Phase 4.

---

## Phase 4 · Consolidated review gate

Show ALL accumulated changes from the three layers — plus any missing
commands detected in Phase 3.5, if applicable — in a single preview before
writing any file. The agent builds the final AGENTS.md in memory (with
all Layer 1 + Layer 2 + Layer 3 changes applied) and shows it complete.

```
Consolidated change summary:

AGENTS.md:
- Layer 1: [list of project content diffs if applicable]
- Layer 2: injected "Local Orchestration" section in Behavior preferences
- Layer 2: footer updated: wf-version 2.1 → 2.4
- Layer 3: [injected Decision Ladder / no Layer 3 changes]

Modified satellites:
- [list of satellites if applicable, or "none"]

Added commands (Phase 3.5):
- [list of new commands per IDE if applicable, or "none — already complete"]

Resulting AGENTS.md (complete):
---
[full AGENTS.md content with all changes applied]
---

Write these files and make the commit? [yes / no, abort / let me edit X first]
```

**PAUSE**. Wait for response.

- `yes`: advance to Phase 5 — write and commit.
- `abort`: discard all changes in buffer. Write nothing.
- `let me edit X first`: show the content of X, listen to the change the user requests,
  apply it to the buffer, show the full review again.

---

## Phase 5 · Write and commit

Only if Phase 4 closed with `yes`:

1. Write the updated AGENTS.md (with all Layer 1 + 2 + 3 changes).
2. Write affected satellites if applicable.
3. Write missing commands added in Phase 3.5, if applicable, in the
   correct directory and format for each IDE (see route table in `wf-init.md`).
4. `git add` the modified files, including new commands:
   ```bash
   git add AGENTS.md
   git add -f .claude/ .cursor/ .windsurf/ .devin/ .kiro/ .opencode/ 2>/dev/null || true
   git add -f .github/copilot-instructions.md .github/prompts/ 2>/dev/null || true
   ```
5. `git commit -m "chore: refresh workflow to v<X.Y>

   - Inject short-plan rule in Behavior preferences
   - [other Layer 1/2/3 changes if applicable]
   - [commands added in Phase 3.5 if applicable, e.g. Add wf-worktree command]"`
6. Do NOT `git push`.

**Final output**:

```
Refresh complete.
- Commit: <hash>
- Updated files: <list>
- Local version updated: <old version> → 3.23
- Active features: <features with =yes>
- Skipped features: <features with =no>

Next steps:
1. Open your AI IDE. The new rules will be active.
2. Ask the agent for a task to validate that it respects `wf-orchestrator` (loads `wf-ladder`/`wf-sdd-trigger` as applicable, classifies into `wf-no-sdd`/`wf-force-sdd`, and emits `wf-preflight`).
```

---

## Additional technical rules

### Protecting custom content with `<!-- WF: DO NOT REGENERATE -->`

If the user has edited AGENTS.md to add custom rules, policies, or team-specific configurations:

**Syntax**:
```markdown
<!-- WF: DO NOT REGENERATE -->
## Your Custom Section

Your content here. The wizard will never touch this.
<!-- /WF: DO NOT REGENERATE -->
```

**How refresh handles it**:
1. Layer 1 (project drift): skips sections inside markers
2. Layer 2 (mandatory changes): skips sections inside markers
3. Layer 3 (optional features): skips sections inside markers

**Result**: custom content is NEVER overwritten, even across major wizard versions.

This is the recommended way to maintain team-specific rules without having them erased by updates.

---

- **User custom content detection**: if in any section you detect content that does not
  match the standard template but appears intentional, ask the user
  before modifying it instead of overwriting.
- **If the user has a wf-version higher than the hardcoded one**: stop and report "your
  AGENTS.md is from a newer version than the current refresh. Update the wizard
  with `brew upgrade gentle-ai` or re-download the latest wf-refresh.md."

---
