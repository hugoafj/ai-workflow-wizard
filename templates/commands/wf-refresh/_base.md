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

# Durable per-project state dir: resume marker + pending prompts + review file.
# It MUST live outside WF_DIR — the bootstrap wipes WF_DIR at the start of every
# run and resume state has to survive that wipe (field report M3: a documented
# re-run before resuming used to destroy .wizard-pending-prompts and
# .wizard-resume-phase). The cksum suffix discriminates projects sharing /tmp.
export WF_STATE_DIR="${TMPDIR:-/tmp}/wf-refresh-state-$(printf %s "$(pwd)" | cksum | cut -d' ' -f1)"
mkdir -p "$WF_STATE_DIR"

# Cleanup trap: ensure staging/plan/baseline are removed on ANY exit (success, error, exit 3)
# Covers early exits from R-1 (exit 3), R5 (exit 3), or any failure.
_cleanup_all() {
  rm -rf "${WF_DIR:-/tmp/wf-refresh-phases}"
  rm -f refresh-plan.json
  rm -f .wizard-refresh-baseline.json
  rm -rf .wizard-staging
}
trap _cleanup_all EXIT

if [[ -s "$WF_STATE_DIR/.wizard-resume-phase" ]]; then
  echo "ℹ Previous refresh interrupted at phase: $(cat "$WF_STATE_DIR/.wizard-resume-phase")"
  echo "  Re-run with WF_REFRESH_RESUME=1 to resume it."
fi

echo "Downloading refresh files from GitHub..."
echo "Source: ${WIZARD_REPO}@${WIZARD_BRANCH}/wf-init/"

curl -fsSL "${WF_RAW}/wf-init/lib/refresher.md" > "${WF_DIR}/lib/refresher.md" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/lib/state.md" > "${WF_DIR}/lib/state.md" 2>/dev/null || true
# NOTE: state-helpers.sh is NOT downloaded here on purpose. The
# "Setup: create helper library" section of refresher.md downloads it
# (with fallbacks) when it writes lib/refresh-lib.sh below.
curl -fsSL "${WF_RAW}/wf-init/lib/builder.md" > "${WF_DIR}/lib/builder.md" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/lib/builder-core.py" > "${WF_DIR}/lib/builder-core.py" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/lib/builder-heavy.py" > "${WF_DIR}/lib/builder-heavy.py" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/phase6a-agents.md" > "${WF_DIR}/phase6a-agents.md" 2>/dev/null || true
curl -fsSL "${WF_RAW}/wf-init/phase6b-build-heavy.md" > "${WF_DIR}/phase6b-build-heavy.md" 2>/dev/null || true
mkdir -p "${WF_DIR}/temp-files"
curl -fsSL "${WF_RAW}/temp-files/AGENTS.md" > "${WF_DIR}/temp-files/AGENTS.md" 2>/dev/null || true

REQUIRED_FILES=(
  "${WF_DIR}/lib/refresher.md"
  "${WF_DIR}/lib/builder.md"
  "${WF_DIR}/lib/builder-core.py"
  "${WF_DIR}/lib/builder-heavy.py"
  "${WF_DIR}/phase6a-agents.md"
  "${WF_DIR}/phase6b-build-heavy.md"
  "${WF_DIR}/temp-files/AGENTS.md"
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
  local phase_name="${1}"
  local out_file="${2}"
  local refresher="${WF_DIR}/lib/refresher.md"

  # Extract ALL fenced bash blocks of the phase, concatenated in order.
  # Header match is prefix-with-boundary: "Phase R-1" matches
  # "## Phase R-1: Global command refresh" but would not match a hypothetical
  # "## Phase R-10". Blocks are self-contained (each re-declares WF_DIR and
  # re-sources refresh-lib.sh) and designed to run sequentially, so
  # concatenation preserves execution order and per-block fail-fast.
  #
  # PLACEHOLDER-SAFE: this program deliberately uses a getline loop in BEGIN
  # instead of pattern rules. Before an agent sees a command body, OpenCode
  # expands every "dollar + digits" token as a positional-argument placeholder
  # (packages/opencode/src/session/prompt.ts, placeholderRegex /\$(\d+)/g):
  # with no arguments, awk's current-record field is injected as the literal
  # string "undefined" and shell positionals become empty strings, which
  # silently destroyed this extraction. A getline loop needs no awk field
  # variables at all. For the same reason, shell positional parameters below
  # use the brace form (invisible to that regex, identical in bash).
  awk -v phase="$phase_name" -v srcfile="$refresher" '
    BEGIN {
      re = "^## " phase "([[:space:]]*:|[[:space:]]*$)"
      in_phase = 0; in_block = 0; found = 0
      while ((getline line < srcfile) > 0) {
        if (!in_phase) {
          if (line ~ re) { in_phase = 1 }
          continue
        }
        if (line ~ re) continue
        if (line ~ /^## /) exit
        if (line ~ /^```bash/) {
          if (found++) printf "\n# --- block %d ---\n", found
          in_block = 1
          continue
        }
        if (in_block && line ~ /^```/) { in_block = 0; continue }
        if (in_block) print line
      }
      close(srcfile)
    }
  ' > "$out_file"

  # Defense in depth: verify block coverage. A silent truncation here used to
  # surface much later as wrong plan classifications (R3 block 2 never ran ->
  # files were classified deleted_modified instead of updated). Die loudly
  # at extraction time instead.
  local total extracted
  total=$(awk -v phase="$phase_name" -v srcfile="$refresher" '
    BEGIN {
      re = "^## " phase "([[:space:]]*:|[[:space:]]*$)"
      in_phase = 0; c = 0
      # NOTE: break, not exit — exit inside BEGIN would end the whole
      # program and skip the final count print.
      while ((getline line < srcfile) > 0) {
        if (!in_phase) { if (line ~ re) in_phase = 1; continue }
        if (line ~ re) continue
        if (line ~ /^## /) break
        if (line ~ /^```bash/) c++
      }
      close(srcfile)
      print c + 0
    }
  ')
  if [[ -s "$out_file" ]]; then
    # grep -c exits 1 when the count is 0 (single-block phases emit no
    # markers). Plain arithmetic would propagate that status and kill any
    # caller invoking this function WITHOUT the `||` suppression while set -e
    # is active. Tolerate it explicitly so extraction context never matters.
    local marker_count
    marker_count=$(grep -c '^# --- block' "$out_file" || true)
    extracted=$(( ${marker_count:-0} + 1 ))
  else
    extracted=0
  fi
  if [[ "$total" -eq 0 || "$extracted" -ne "$total" ]]; then
    echo "✗ Failed to extract $phase_name: got $extracted/$total bash blocks" >&2
    return 1
  fi
  chmod +x "$out_file"
  return 0
}

# Execute a phase script with proper error handling
# Usage: _run_phase "Phase R-1" "phase-r1.sh"
_run_phase() {
  local phase_name="${1}"
  local script_file="${2}"
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
# Setup: build the shared helper library BEFORE any phase runs. Every phase
# sources ${WF_DIR}/lib/refresh-lib.sh, and that file is written by the
# "Setup: create helper library" section of refresher.md. Without running it
# first, Phase R-1 dies with:
#   /tmp/wf-refresh-phases/lib/refresh-lib.sh: No such file or directory
_extract_phase "Setup: create helper library" "${WF_DIR}/phase-setup.sh" || exit $?
_run_phase "Setup: create helper library" "${WF_DIR}/phase-setup.sh" || exit $?

# Phase R-1: Global command refresh
_extract_phase "Phase R-1" "${WF_DIR}/phase-r1.sh"
# R-1 can exit 3 = "global commands updated, restart required".
# Handle it explicitly: show clear message and exit 0 (not error).
if bash "${WF_DIR}/phase-r1.sh"; then
  echo "✓ Phase R-1 completed"
else
  exit_code=$?
  if [[ $exit_code -eq 3 ]]; then
    echo ""
    echo "⚠ Global commands updated to the latest version."
    echo "  The wizard code downloaded at session start is now stale."
    echo "  Open a NEW terminal and re-run /wf-refresh so the updated wizard drives the refresh."
    echo ""
    exit 0
  fi
  echo "✗ Phase R-1 failed with exit code $exit_code" >&2
  exit $exit_code
fi

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

### Phase R-1 exits with code 3 (global command update)

- **Issue**: In a non-interactive run, the `Update global commands?` answer was missing. R-1 emits `GENTLE_AI_WF_REFRESH_NEEDS=prompt=Update global commands?` and stops BEFORE any refresh work — this is expected control flow, not a crash.
- **Solution**: Ask the user, set `WF_REFRESH_ANSWERS='Update global commands?=yes'` (or `=no`) and re-run with `WF_REFRESH_RESUME=1`. If the answer is `yes` and `install.sh` succeeds, R-1 exits 3 again: open a NEW session and re-run `/wf-refresh` so the updated wizard drives the refresh.

### Phase R1/R2 exits with code 3 (drift / feature prompts)

- **Issue**: In a non-interactive run, `Use updated project info?` (R1) or `Enable <FEATURE>?` (R2) had no answer. The phase stops IMMEDIATELY — before staging is built — and emits `GENTLE_AI_WF_REFRESH_NEEDS=prompt=...`. This is expected control flow: continuing would build staging from stale info and the answer collected later would have no consumer.
- **Solution**: Set `WF_REFRESH_ANSWERS='Use updated project info?=yes'` (or `=no`, or the matching `Enable <FEATURE>?` prompt) and re-run with `WF_REFRESH_RESUME=1`. The run re-enters exactly the phase that asked (tracked via `.wizard-resume-phase`), consumes your answer, and continues through R5 normally.

### Phase R5 exits with code 3 (review prompts and/or apply mode)

- **Issue**: In a non-interactive run, review prompts (`Apply added files?`, `Apply updated files?`, `Delete removed files?`, `Delete these modified files?`, `Overwrite locally-modified files?`, `Append these .gitignore entries...`) and/or the apply decision were unanswered. R5 emits ONE manifest listing everything still missing — `GENTLE_AI_WF_REFRESH_NEEDS=prompt=...|apply_mode=` — and stops BEFORE applying anything. This is expected control flow.
- **Solution**: Set `WF_REFRESH_ANSWERS='Apply added files?=yes|Apply updated files?=no'` using the exact prompt strings from the manifest, AND set `WF_REFRESH_APPLY_MODE`, then re-run with `WF_REFRESH_RESUME=1`. Already-answered prompts drop off the list automatically on the next pass.

### Apply gate: WF_REFRESH_APPLY_MODE

Before applying (Phase R5 → R6), a non-tty run requires an explicit decision:
- `WF_REFRESH_APPLY_MODE=commit` — apply approved changes and commit them
- `WF_REFRESH_APPLY_MODE=apply-only` — apply to the working tree, NO commit
- `WF_REFRESH_APPLY_MODE=cancel` — discard staging; nothing is written

A missing value emits `GENTLE_AI_WF_REFRESH_NEEDS=apply_mode=` with exit 3 (same contract as every other gate).

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

## Agent / Copilot Integration Guide

The following sections explain how AI agents (GitHub Copilot, Claude Code, etc.) should handle the `/wf-refresh` non-interactive protocol. This is not a bug — it is the designed contract for headless/agent-driven runs.

### Agent Handling: Phase R-1 exits with code 3 (global command updated)

- **What happens**: R-1 runs `install.sh` successfully and exits with code 3. This means "the wizard binary/global commands have been updated; the code downloaded at session start is now stale."
- **Agent MUST**: 
  1. Capture the output (it contains "Global commands updated to X.Y.Z")
  2. Present this message to the user clearly: "⚠ Global commands updated. Open a NEW terminal and re-run /wf-refresh"
  3. **DO NOT** re-run the same orchestrator script — it still holds the old downloaded phase scripts
  4. **DO NOT** treat exit 3 as an error
- **Why**: The orchestrator downloads phase scripts ONCE at startup. After `install.sh`, the on-disk global commands are new, but the in-memory `/tmp/wf-refresh-phases/*` scripts are old. A fresh session picks up the new versions.

### Agent Handling: GENTLE_AI_WF_REFRESH_NEEDS manifest (exit 3 from R1/R2/R5)

- **What happens**: A phase emits `GENTLE_AI_WF_REFRESH_NEEDS=prompt=...|apply_mode=` and exits 3. This is the protocol asking for user decisions.
- **Agent MUST**:
  1. Parse the manifest (format: `prompt=Question?|prompt=Question2?|apply_mode=`)
  2. Present each prompt to the user with clear context (what is being approved, what files affected)
  3. Collect yes/no answers from the user
  4. Set `WF_REFRESH_ANSWERS='Prompt A=yes|Prompt B=no|...'` and `WF_REFRESH_APPLY_MODE=commit|apply-only|cancel`
  5. Re-run the orchestrator with `WF_REFRESH_RESUME=1`
- **Why**: The protocol is designed for exactly this — the agent is the interactive bridge between the headless script and the human.

### Agent Handling: Do NOT run phases in background without capturing output

- **Anti-pattern**: `bash phase-r5.sh &` or any fire-and-forget that discards stdout/stderr
- **Correct**: Run each phase synchronously, capture full output, parse for `GENTLE_AI_WF_REFRESH_NEEDS`, then act on it.
- **Why**: The prompts and manifest are emitted to stdout. Background execution loses them, leaving the user confused and the refresh stuck.

---

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
