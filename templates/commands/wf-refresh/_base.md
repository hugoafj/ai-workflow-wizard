# /wf-refresh — Builder-driven refresh

⚡ **AUTOMATION**: Phases R-1 and R0 run automatically. R1, R2, and R5 prompt you (drift/feature approvals); R3/R4/R6 run autonomously.

---

> Deterministic refresh that re-runs the Builder to detect and apply changes to your project.
> Replaces the old Layer 1/2/3 approach with a single source of truth: the Builder.
> Works as a complement to `/wf-init`. Assumes /wf-init already ran in this repo before.
>
> Source: github.com/hugoafj/ai-workflow-wizard

## What this refresh does

Detects project drift and applies updates safely:

1. **Phase R-1**: Update global commands (`wf-init`, `wf-refresh`, `wf-cleanup`) if outdated
2. **Phase R0**: Validate `.wizard-state.json` and detect active IDEs
3. **Phase R1**: Re-discover project (stack, node engine, etc.) and detect drift
4. **Phase R2**: Migrate state schema and ask about new optional features
5. **Phase R3**: Re-run Builder (B1-B9) to generate all artifacts into `.wizard-staging/` (first snapshots the pre-Builder `managed_paths`/`generated_files` into `.wizard-refresh-baseline.json`)
6. **Phase R4**: Compare the R3 baseline snapshot with staging using SHA256 hashes; classify files as add/update/delete/unchanged, with `deleted_modified` flagged when the user edited a file since the last refresh
7. **Phase R5**: Show a real content preview (added → staged content; updated → `diff -u` against staging; deleted/deleted_modified → current content) and collect your approvals
8. **Phase R6**: Apply approved changes only; on approval update state, write `.wizard-managed-files.json`, and commit via an explicit pathspec; a fully declined refresh writes nothing

---

## How /wf-refresh works

**Automation + Human guidance**:
- **Phases R-1 & R0** (automated): Execute version checks and validations automatically
- **Phases R1–R6** (interactive): Analyze and propose changes; pause for user approval

**Your role as the agent**:

1. **Execute Phase R-1** (global command refresh): Check versions, propose update if needed
2. **Execute Phase R0** (validation): Verify `.wizard-state.json` exists and is valid
3. **Execute Phases R1–R6** in sequence, pausing for user approval at Phase R5

**Inviolable rules**:

1. Do NOT apply changes without explicit user OK at Phase R5
2. Do NOT `git add` or `git commit` until Phase R6 (after approvals)
3. Show clear diffs before applying any changes
4. Respect content marked with `<!-- WF: DO NOT REGENERATE -->`
5. Never delete user skills or custom content without explicit approval
6. If a user response is ambiguous, ask again

---

## Implementation

Download the refresh orchestrator and supporting files, then read and execute each phase in `refresher.md` in order. **Do NOT `source` Markdown files** — read them as instructions and execute the fenced bash blocks one at a time.

**CRITICAL**: To avoid heredoc/escaping issues (especially with jq filters containing nested quotes), each phase script MUST be written to a temporary file and executed with `bash /path/to/file.sh` — never executed inline via `bash -c '...'` or heredoc.

```bash
#!/bin/bash
set -e

# Signals the Builder phases that this run is a refresh: phase6b Step 5 then
# skips the phase7 pointer promotion and phase7.md handoff (see refresher.md R3
# and phase6b-build-heavy.md Step 5). Without it, a refresh would advance the
# pointer to phase7 and derail into wf-init's review/promotion flow.
export WF_REFRESH=1

# Verify .wizard-state.json exists
if [[ ! -f .wizard-state.json ]]; then
  echo "✗ .wizard-state.json not found"
  echo "  Please run /wf-init first"
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "✗ Not a git repository"
  exit 1
fi

# Wizard repository
WIZARD_REPO="hugoafj/ai-workflow-wizard"
WIZARD_BRANCH="main"
WF_RAW="https://raw.githubusercontent.com/${WIZARD_REPO}/${WIZARD_BRANCH}"

# Local directory for downloaded refresh files (temporary, can be cleaned later)
WF_DIR="/tmp/wf-refresh-phases"
rm -rf "$WF_DIR"
mkdir -p "$WF_DIR"
mkdir -p "$WF_DIR/lib"

echo "Downloading refresh files from GitHub..."
echo "Source: ${WIZARD_REPO}@${WIZARD_BRANCH}/wf-init/"

curl -fsSL "${WF_RAW}/wf-init/lib/refresher.md" > "${WF_DIR}/lib/refresher.md" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/lib/state.md" > "${WF_DIR}/lib/state.md" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/lib/state-helpers.sh" > "${WF_DIR}/lib/state-helpers.sh" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/lib/builder.md" > "${WF_DIR}/lib/builder.md" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/lib/builder-core.py" > "${WF_DIR}/lib/builder-core.py" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/lib/builder-heavy.py" > "${WF_DIR}/lib/builder-heavy.py" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/phase6a-agents.md" > "${WF_DIR}/phase6a-agents.md" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/phase6b-build-heavy.md" > "${WF_DIR}/phase6b-build-heavy.md" 2>/dev/null || true
mkdir -p "${WF_DIR}/temp-files"
curl -fsSL "${WF_RAW}/temp-files/AGENTS.md" > "${WF_DIR}/temp-files/AGENTS.md" 2>/dev/null || true
curl -fsSL "${WF_RAW}/temp-files/sdd-new.md" > "${WF_DIR}/temp-files/sdd-new.md" 2>/dev/null || true

REQUIRED_FILES=(
  "${WF_DIR}/lib/refresher.md"
  "${WF_DIR}/lib/state-helpers.sh"
  "${WF_DIR}/lib/builder.md"
  "${WF_DIR}/lib/builder-core.py"
  "${WF_DIR}/lib/builder-heavy.py"
  "${WF_DIR}/phase6a-agents.md"
  "${WF_DIR}/phase6b-build-heavy.md"
  "${WF_DIR}/temp-files/AGENTS.md"
  "${WF_DIR}/temp-files/sdd-new.md"
)

missing=false
for f in "${REQUIRED_FILES[@]}"; do
  if [ ! -s "$f" ]; then
    echo "✗ Could not download $(basename "$f") from GitHub" >&2
    missing=true
  fi
done

if [ "$missing" = true ]; then
  exit 1
fi

echo "✓ Refresh files downloaded to: ${WF_DIR}"

# Helper: extract a phase from refresher.md and write to executable temp file
# Usage: _extract_phase "Phase R-1" "phase-r1.sh"
_extract_phase() {
  local phase_name="$1"
  local out_file="$2"
  local refresher="${WF_DIR}/lib/refresher.md"
  
  # Find the phase section and extract the first fenced bash block after it
  awk -v phase="$phase_name" '
    $0 ~ "^## " phase "[[:space:]]*$" { in_phase=1; next }
    in_phase && /^```bash/ { in_block=1; next }
    in_block && /^```/ { exit }
    in_block { print }
  ' "$refresher" > "$out_file"
  
  if [[ ! -s "$out_file" ]]; then
    echo "✗ Failed to extract $phase_name from refresher.md" >&2
    return 1
  fi
  chmod +x "$out_file"
  return 0
}

# Execute a phase script with proper error handling
# Usage: _run_phase "Phase R-1" "phase-r1.sh"
_run_phase() {
  local phase_name="$1"
  local script_file="$2"
  echo "=== Executing $phase_name ==="
  if bash "$script_file"; then
    echo "✓ $phase_name completed"
    return 0
  else
    local exit_code=$?
    echo "✗ $phase_name failed with exit code $exit_code" >&2
    return $exit_code
  fi
}
```

Now read the orchestrator and execute each phase in order using the helper functions:

```bash
# Phase R-1: Global command refresh
_extract_phase "Phase R-1" "${WF_DIR}/phase-r1.sh"
_run_phase "Phase R-1" "${WF_DIR}/phase-r1.sh" || exit $?

# Phase R0: Project validation
_extract_phase "Phase R0" "${WF_DIR}/phase-r0.sh"
_run_phase "Phase R0" "${WF_DIR}/phase-r0.sh" || exit $?

# Phase R1: Project content drift
_extract_phase "Phase R1" "${WF_DIR}/phase-r1-drift.sh"
_run_phase "Phase R1" "${WF_DIR}/phase-r1-drift.sh" || exit $?

# Phase R2: State/schema migration
_extract_phase "Phase R2" "${WF_DIR}/phase-r2.sh"
_run_phase "Phase R2" "${WF_DIR}/phase-r2.sh" || exit $?

# Phase R3: Build new staging (Step 0 + Builder + validation)
_extract_phase "Phase R3" "${WF_DIR}/phase-r3.sh"
_run_phase "Phase R3" "${WF_DIR}/phase-r3.sh" || exit $?

# Phase R4: Diff and plan
_extract_phase "Phase R4" "${WF_DIR}/phase-r4.sh"
_run_phase "Phase R4" "${WF_DIR}/phase-r4.sh" || exit $?

# Phase R5: Review gate
_extract_phase "Phase R5" "${WF_DIR}/phase-r5.sh"
_run_phase "Phase R5" "${WF_DIR}/phase-r5.sh" || exit $?

# Phase R6: Apply and close
_extract_phase "Phase R6" "${WF_DIR}/phase-r6.sh"
_run_phase "Phase R6" "${WF_DIR}/phase-r6.sh" || exit $?
```

Each phase script is extracted from `refresher.md` and executed as a standalone bash file, avoiding all heredoc/escaping issues.

---

## Troubleshooting

### Phase R-1 fails (global command update)

- **Issue**: `install.sh` not found or fails
- **Solution**: Run `install.sh` manually or skip the update (you can run it later)

### Phase R0 fails (validation)

- **Issue**: `.wizard-state.json` missing or invalid
- **Solution**: Run `/wf-init` first to initialize the project

### Phase R1 fails (project drift)

- **Issue**: Discovery commands fail
- **Solution**: Check that `package.json`, `git`, and other project files are accessible

### Phase R2 fails (state migration)

- **Issue**: Schema migration fails
- **Solution**: Run `/wf-cleanup` and `/wf-init` to reset the project

### Phase R3 fails (Builder)

- **Issue**: Builder fails to generate staging
- **Solution**: Check `.wizard-state.json` for validity; may need `/wf-cleanup` + `/wf-init`

### Phase R5 (review gate)

- **Issue**: Diff looks wrong or incomplete
- **Solution**: Review the diff carefully; you can reject changes and re-run `/wf-refresh` later

### Phase R6 fails (apply)

- **Issue**: Git operations fail
- **Solution**: Check git status; may need to commit or stash changes first

---

## Key concepts

### Hash-based diff

Each file in staging is compared with the project using SHA256 hashes:
- **Unchanged**: Hash matches → file is skipped (not re-copied)
- **Updated**: Hash differs → file is proposed for update
- **Added**: File only in staging → proposed for addition
- **Deleted**: File only in project and marked as wizard-managed, unchanged → proposed for deletion
- **Deleted-modified**: File in old `managed_paths`, not in new staging, but project hash differs from recorded hash → flagged for explicit approval

### Wizard-managed files

Files that the wizard owns and can manage:
- `wf-*/SKILL.md` (wizard skills)
- `.agents/skills/wf-*` (universal wizard skills)
- `.claude/skills/wf-*`, `.cursor/skills/wf-*`, etc. (per-IDE wizard skills)
- `.agents/protocols/wf-*` (wizard protocols)
- `.github/workflows/release-please.yml`, `.github/workflows/quality-guard.yml`, etc.
- `.husky/post-commit`, `.husky/commit-msg`
- `AGENTS.md`, `vitest.config.ts`, `playwright.config.ts`, etc.

User skills and custom content are never deleted.

### Custom AGENTS.md preservation

Sections inside `<!-- WF: DO NOT REGENERATE -->` markers are preserved:

```markdown
# AGENTS.md — my-project

<!-- WF: DO NOT REGENERATE -->
## Custom section

This section is maintained by me and will not be overwritten by /wf-refresh.
<!-- /WF: DO NOT REGENERATE -->

## Wizard-managed section

This section is regenerated by /wf-refresh.
```

---

## Next steps

After refresh completes:

1. Review the commit: `git log -1 -p`
2. If satisfied: `git push` (when ready)
3. If issues: `git revert HEAD` and re-run `/wf-refresh`

---

## Related commands

- `/wf-init` — Initialize a new project with the wizard
- `/wf-cleanup` — Remove all wizard artifacts and reset the project
- `/wf-settings` — Configure wizard options
