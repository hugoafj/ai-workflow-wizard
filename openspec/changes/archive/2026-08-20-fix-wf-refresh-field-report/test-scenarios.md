# Test Scenarios: Fix `/wf-refresh` field-report defects (FU1–FU7)

**Change**: `fix-wf-refresh-field-report`  
**Status**: Test Scenarios  
**Created**: 2026-08-20

## Overview

These test scenarios verify the seven field-report fixes (FU1–FU7) plus R2 normalization and doc-sync. Verification uses `bash -n`, `python3 -m py_compile`, and scripted fixture dry-runs (proposal success criteria a–e). No test runner exists (markdown repo, strict TDD false).

---

## Scenario A: FU1 + R2 — Node/npm defaults coalesce and corrupt state self-heals

**Purpose**: Verify coalescing at builder boundary and R2 normalization of already-corrupted state.

**Setup**:
- Temp git repo initialized with `/wf-init` (or minimal `.wizard-state.json`)
- `package.json` WITHOUT `engines.node`
- Corrupt state: `discovery.node_engine = "None"`, `discovery.npm_major = ""` (or missing keys entirely)

**Execution**:
```bash
# Dry-run builder-heavy directly on temp project
cd /tmp/test-fu1
python3 -m py_compile wf-init/lib/builder-core.py wf-init/lib/builder-heavy.py
# Simulate builder render of quality-guard.yml
python3 -c "
import sys; sys.path.insert(0, 'wf-init/lib')
from builder_heavy import BuilderHeavy
b = BuilderHeavy('/tmp/test-fu1')
# ... invoke quality-guard render
"
# OR: run /wf-refresh on temp project and inspect staging/quality-guard.yml
```

**Expected outcome**:
- `quality-guard.yml` contains `node-version: "22"` (never `""` or `"None"`)
- `quality-guard.yml` contains `npm install -g npm@10` (never `npm@""` or `npm@"None"`)
- Deploy workflow (if cd enabled) uses same resolution
- R2 migration normalizes `"None"`/`""` → `null`/absent on next refresh
- Real `engines.node = "20.x"` in package.json is honored (defaults never override)

**Acceptance criteria**:
- [ ] Missing keys → defaults `22`/`10`
- [ ] Empty string/null → defaults `22`/`10`
- [ ] Literal `"None"` → defaults `22`/`10` (self-heals)
- [ ] Real `engines.node` honored
- [ ] Deploy variant shares resolution
- [ ] R1 never clobbers good value with empty discovery result
- [ ] R2 normalization idempotent on clean state

---

## Scenario B: FU2 + FU3a — Stale commands replaced by merged bullets

**Purpose**: Verify R1 always re-detects from `package.json` and renders merged bullets with descriptions.

**Setup**:
- Project with `package.json` defining 12 scripts: `dev`, `build`, `test`, `lint`, `format`, `typecheck`, `clean`, `prepublish`, `start`, `postinstall`, `prepare`, `release`
- Existing `.wizard-state.json` with stale `discovery.commands` listing only 4 scripts: `dev`, `build`, `test`, `lint`
- Current `AGENTS.md` has Commands section with descriptions for `dev` and `build` only

**Execution**:
```bash
cd /tmp/test-fu2
# Run R1 block of refresher.md in isolation (or full /wf-refresh)
bash -n wf-init/lib/refresher.md
# Extract and run R1 commands detection + merge logic
```

**Expected outcome**:
- Fresh detection produces all 12 scripts
- Drift gate fires: `Commands: <old 4> → <new 12>`
- Accepted drift writes fresh 12-script list to staging state
- Regenerated AGENTS.md Commands section renders as bullets:
  - `- npm run dev — dev server` (description from old AGENTS.md)
  - `- npm run build — production build` (description from old AGENTS.md)
  - `- npm run test` (no description — new script)
  - `- npm run lint` (no description — had no description in old)
  - ... all 12 scripts present, none dropped
- Scripts removed from package.json disappear from regenerated section

**Acceptance criteria**:
- [ ] Stale partial list replaced by full fresh list
- [ ] Drift gate fires on difference
- [ ] Accepted drift writes fresh list to staging
- [ ] Known scripts keep parsed descriptions
- [ ] New scripts render without description
- [ ] No package.json script is dropped
- [ ] Removed scripts disappear
- [ ] No package.json → falls back to stored list, no drift reported
- [ ] Identical list → no-op, no rewrite

---

## Scenario C: FU3b + FU3c + FU3d — Rich sections regenerate and survive round-trip

**Purpose**: Verify Code Style composes from conventions, Structure from live tree, MCPs render 3-col with Purpose/Required-setup preserved.

**Setup**:
- Project with nested structure: `src/lib/`, `src/components/`, `templates/`, `wf-init/lib/`, `tests/`
- Old AGENTS.md Structure section has comment: `templates/ — single source of truth`
- `discovery.conventions` has: `naming: kebab-case`, `components: atomic`, `tests: vitest`, `css: tailwind`
- MCP configs: `.mcp.json` with `playwright`, `.cursor/mcp.json` with `github`
- Old AGENTS.md MCP table has: `| Playwright | Browser control for E2E | npx playwright install --with-deps chromium |`

**Execution**:
```bash
cd /tmp/test-fu3
bash -n wf-init/lib/refresher.md
python3 -m py_compile wf-init/lib/builder-core.py
# Run R1 structure/MCPs regeneration + builder render
```

**Expected outcome**:
- **Code Style**: renders bullets `- Naming: kebab-case`, `- Components: atomic`, `- Tests: vitest`, `- CSS: tailwind` (no `camelCase` fallback)
- **Structure**: tree includes all live dirs; `templates/` line retains comment `— single source of truth`; new paths (e.g., `src/lib/new.ts`) appear without comment
- **MCPs**: 3-column table `| MCP | Purpose | Required setup |` with Playwright row preserving Purpose and Required-setup; GitHub MCP renders with Purpose/Required-setup if known, else 2-col fallback
- Round-trip: run refresh again → Purpose/Required-setup still present (not flattened to 2-col)

**Acceptance criteria**:
- [ ] Code Style composes from structured conventions when present
- [ ] Absent conventions → preserves existing AGENTS.md section verbatim
- [ ] Structure regenerates from live tree (capped depth, exclusions)
- [ ] Matching comments survive by path-name match
- [ ] MCPs re-detected from config files
- [ ] Purpose/Required-setup merged from old AGENTS.md table
- [ ] 3-col table rendered when purpose present, 2-col fallback otherwise
- [ ] New MCP appends without dropping existing rows
- [ ] Rich 3-col table survives round-trip (no Purpose/Required-setup loss)

---

## Scenario D: FU6 — Apply-only deletions are unstaged with truthful message

**Purpose**: Verify apply-only mode uses plain `rm -f` for deletions, never `git rm`, and closing message is accurate.

**Setup**:
- Project with refresher staging containing: 2 `updated` files, 1 `new` file, 2 `deleted` files, 1 `deleted_modified` file
- Run in apply-only mode (`APPLY_ONLY=true`)

**Execution**:
```bash
cd /tmp/test-fu6
# Run R6 apply block with APPLY_ONLY=true
APPLY_ONLY=true bash -c '...R6 apply logic...'
git status
```

**Expected outcome**:
- `updated`/`new` files copied with `cp` (unstaged)
- `deleted`/`deleted_modified` files removed with `rm -f` (unstaged)
- `git status` shows ALL changes as unstaged (including deletions)
- Closing message: "changes left in the working tree (unstaged)"
- Commit mode (default): `git rm -f` stages deletions; commit contains them

**Acceptance criteria**:
- [ ] Apply-only: deletions use `rm -f`, unstaged
- [ ] Apply-only: `git status` shows deletions unstaged
- [ ] Apply-only: closing message accurate ("unstaged")
- [ ] Commit mode: `git rm` stages deletions
- [ ] Apply-only with zero deletions: no git ops, message accurate
- [ ] `deleted_modified` also uses plain `rm -f` in apply-only

---

## Scenario E: FU7 — Locally-modified updated files flagged and gated

**Purpose**: Verify `local_modified` flag on updated files with uncommitted changes, dedicated warning block, and overwrite approval gate.

**Setup**:
- Project with `AGENTS.md` having uncommitted local edits (working tree ≠ HEAD)
- Refresher staging has `AGENTS.md` as `updated` entry
- Non-git fallback: project without git, compare against `old_hash`

**Execution**:
```bash
cd /tmp/test-fu7
# Make local edit to AGENTS.md
echo "# Local edit" >> AGENTS.md
# Run R4 classification + R5 review gate + R6 apply
bash -n wf-init/lib/refresher.md
# Simulate R4/R5/R6 with local_modified logic
```

**Expected outcome**:
- R4: `AGENTS.md` plan entry has `local_modified: true`
- R5: dedicated warning block lists `AGENTS.md` under "Locally-modified files:"
- R5: dedicated prompt `Overwrite locally-modified files?` (stored as `build_plan.approval.overwrite_local`)
- R6: if approval `no` → `AGENTS.md` NOT overwritten; other approved files still applied
- R6: if approval `yes` → `AGENTS.md` overwritten with staged version
- Clean updated file (identical to HEAD): no `local_modified` flag, only normal updated approval
- Non-git project with matching `old_hash`: treated as plain `updated` (no extra gate)

**Acceptance criteria**:
- [ ] Local edits → `local_modified: true` in plan
- [ ] Dedicated warning block in R5
- [ ] Dedicated overwrite approval prompt
- [ ] Overwrite declined → local file kept, other files applied
- [ ] Overwrite approved → file replaced
- [ ] Clean updated file skips extra gate
- [ ] Non-git fallback works (hash compare)
- [ ] `refresh-plan.json` schema has `local_modified` boolean (default false, backwards-compatible)

---

## Scenario F: FU4 — DEPRECATED_PATHS covers per-IDE skills

**Purpose**: Verify per-IDE skill dirs for 6 deprecated commands are classified for deletion.

**Setup**:
- Project with orphan skill files on disk (not in staging):
  - `.claude/skills/wf-init/SKILL.md`
  - `.cursor/skills/wf-cleanup/SKILL.md`
  - `.opencode/skills/wf-refresh/SKILL.md`
  - `.windsurf/skills/wf-cicd/SKILL.md`
  - `.codex/skills/wf-sdd-config/SKILL.md`
  - `.kiro/skills/wf-sdd-lite/SKILL.md`
  - `.github/skills/wf-init/SKILL.md`
  - `.devin/skills/wf-cleanup/SKILL.md` (only when windsurf active)
- Staging does NOT contain these paths

**Execution**:
```bash
cd /tmp/test-fu4
bash -n wf-init/lib/refresher.md
# Run R4 classification
```

**Expected outcome**:
- All 8×6 = 48 paths (minus `.devin` when windsurf inactive) classified as `deleted` with reason `deprecated command`
- Deduplication: path appearing in both baseline and DEPRECATED_PATHS counts once
- Still-current skill (exists in staging) NOT classified `deleted` even if in DEPRECATED_PATHS
- All appear in R5 DELETED block requiring approval

**Acceptance criteria**:
- [ ] Orphan per-IDE skills of 6 deprecated commands listed for deletion
- [ ] `.devin` only when windsurf active
- [ ] Guard: present on disk AND absent from staging
- [ ] Deduplication works
- [ ] Still-current skill never deleted
- [ ] R5 approval gate for deletions preserved

---

## Scenario G: FU5 — Non-tty manifest + resume

**Purpose**: Verify non-tty runs emit structured manifest instead of aborting, and resume re-enters R5 with staging intact.

**Setup**:
- Non-tty environment (no TTY, no `WF_REFRESH_ANSWERS`, no `WF_REFRESH_DEFAULT_ANSWER`)
- Project with drift in R1 (commands) and feature enable in R2

**Execution**:
```bash
cd /tmp/test-fu5
# Run refresher in non-tty (e.g., via script or CI)
# Capture output and exit code
./wf-refresh 2>&1 | head -20
echo "Exit code: $?"
# Check for GENTLE_AI_WF_REFRESH_NEEDS
# Check no orphaned .wizard-staging/, refresh-plan.json, .wizard-refresh-baseline.json
# Then resume:
WF_REFRESH_RESUME=1 ./wf-refresh 2>&1
```

**Expected outcome**:
- Run does NOT `exit 2` mid-pipeline
- Prints `GENTLE_AI_WF_REFRESH_NEEDS="prompt=Use updated project info?|prompt=Enable feature X?|apply_mode=..."` with exit code 3
- No orphaned `.wizard-staging/`, `refresh-plan.json`, `.wizard-refresh-baseline.json` (or exact resume instructions printed)
- `WF_REFRESH_RESUME=1` skips R-1→R4, validates staging/plan exist, re-enters R5 with staging intact
- Supplied `WF_REFRESH_ANSWERS="Use updated project info?=yes"` consumes answer normally, no manifest
- Apply-gate refusal emits manifest, preserves staging for resume (or cleans with resume steps)

**Acceptance criteria**:
- [ ] Unanswered prompt → manifest + exit 3 (not exit 2)
- [ ] Manifest format: `GENTLE_AI_WF_REFRESH_NEEDS="prompt=...|...|apply_mode=..."`
- [ ] No orphaned artifacts (or resume instructions printed)
- [ ] `WF_REFRESH_RESUME=1` skips R-1→R4, re-enters R5 with staging intact
- [ ] Supplied answers avoid manifest
- [ ] Apply-gate refusal is resumable (staging preserved or cleaned with instructions)

---

## Scenario H: FU3e — Preservation is fallback, not gate

**Purpose**: Verify fresh detection supersedes stale preserved text; richer existing content wins over flat state.

**Setup**:
- Staging state has stale preserved `discovery.commands` blob (old flat format) that no longer matches `package.json`
- AGENTS.md has rich multi-line Code Style section; state has flat `code_style: "camelCase"`

**Execution**:
```bash
cd /tmp/test-fu3e
# Run R1 regeneration + builder render
```

**Expected outcome**:
- Commands section reflects fresh `package.json` scripts (not stale blob)
- Code Style uses richer AGENTS.md content (merged with conventions) over flat state value
- Regenerated content supersedes stale preserved text for all derivable fields

**Acceptance criteria**:
- [ ] Fresh detection supersedes stale preserved text
- [ ] Richer existing content wins over flat state
- [ ] Preservation only for non-derivable fields (final fallback)

---

## Manual Verification Checklist

After all fixture dry-runs pass, manually verify:

- [ ] **No user skills deleted**: Check `.claude/skills/`, `.agents/skills/`, etc. user skills preserved in FU4 scenario
- [ ] **Custom AGENTS.md preserved**: Sections with `<!-- WF: DO NOT REGENERATE -->` markers intact
- [ ] **Commit messages conventional**: If commit mode tested, verify format
- [ ] **No push**: Verify no automatic push occurred
- [ ] **Diffs reviewed**: Review all diffs in each scenario before approving
- [ ] **State consistency**: `.wizard-state.json` valid after each refresh
- [ ] **AI_DEV_WORKFLOW.md mirrors code**: R1/R4/R5/R6 sections (709, 762, 765-767, 1699-1710) describe new behavior
- [ ] **Line 765 no longer overstates DEPRECATED_PATHS coverage**

---

## Test Execution

```bash
#!/bin/bash
set -e

echo "=== Scenario A: FU1+R2 coalescing ==="
cd /tmp/test-fu1 && ./run-fu1.sh

echo "=== Scenario B: FU2+FU3a commands ==="
cd /tmp/test-fu2 && ./run-fu2.sh

echo "=== Scenario C: FU3b+c+d rich sections ==="
cd /tmp/test-fu3 && ./run-fu3.sh

echo "=== Scenario D: FU6 apply-only ==="
cd /tmp/test-fu6 && ./run-fu6.sh

echo "=== Scenario E: FU7 local-modified ==="
cd /tmp/test-fu7 && ./run-fu7.sh

echo "=== Scenario F: FU4 DEPRECATED_PATHS ==="
cd /tmp/test-fu4 && ./run-fu4.sh

echo "=== Scenario G: FU5 non-tty manifest/resume ==="
cd /tmp/test-fu5 && ./run-fu5.sh

echo "=== Scenario H: FU3e preservation fallback ==="
cd /tmp/test-fu3e && ./run-fu3e.sh

echo "✓ All scenarios completed"
```

---

## Success Criteria (Overall)

- [ ] All 8 scenarios (A–H) pass
- [ ] `python3 -m py_compile` passes on `builder-core.py`/`builder-heavy.py`
- [ ] `bash -n` passes on every modified refresher block
- [ ] Fixture dry-runs (a)–(e) from proposal all pass
- [ ] Non-tty manifest/resume works
- [ ] `DEPRECATED_PATHS` coverage verified against `meta.md`/`install.sh`
- [ ] `AI_DEV_WORKFLOW.md` R1/R4/R5/R6 sections updated in same change
- [ ] Manual verification checklist completed
- [ ] No commits without user review