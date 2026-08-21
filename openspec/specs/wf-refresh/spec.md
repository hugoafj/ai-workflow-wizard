# Specification: Fix `/wf-refresh` field-report defects (FU1–FU7)

**Change**: `fix-wf-refresh-field-report`
**Status**: Specification
**Created**: 2026-08-20

## Overview

Delta specification for corrective changes to the builder-driven `/wf-refresh` pipeline (`wf-init/lib/refresher.md`, `wf-init/lib/refresh-lib.sh`, `wf-init/lib/builder-core.py`, `wf-init/lib/builder-heavy.py`, `wf-init/lib/state.md`) and its docs. Defects verified against commit `5e8b0e2` (`exploration.md`; FU4 in corrected form).

Three behavioral themes:

1. **Regeneration-first with merge (FU2, FU3a–FU3e)** — R1 re-detects all discoverable fields unconditionally; current `AGENTS.md` is parsed once as a merge source (descriptions/comments/MCP purpose survive where names match); rich sections re-render from structured `discovery.*`; whole-section preservation is the final fallback only.
2. **Coalescing at the builder boundary (FU1, R2)** — empty/`null`/`"None"` `node_engine`/`npm_major` resolve to `"22"`/`"10"`; R1 stops writing empty values; R2 normalizes already-corrupted state.
3. **Safety completions (FU4–FU7)** — extended deprecated-path cleanup; non-tty runs emit a structured pending-prompts manifest with resume instead of bare `exit 2`; apply-only never stages deletions; locally-modified `updated` files require a dedicated overwrite approval.

`AI_DEV_WORKFLOW.md` R1/R4/R5/R6 sections (~709, 762, 765-767, 1699-1710) update in the same change (AGENTS.md sync rule). No test runner (strict TDD false); requirements are verifiable via `bash -n`, `python3 -m py_compile`, and fixture dry-runs (proposal success criteria a–e).

---

## Capability: `wf-refresh`

### Requirement: FU1 — Node/npm defaults coalescing

The builder SHALL resolve `discovery.node_engine`/`discovery.npm_major` through a single coalescing rule (`builder-core.py` `get_state_value`/`_coalesce`): missing key, `null`, `""`, and literal `"None"` all resolve to `"22"`/`"10"`. `quality-guard.yml` SHALL NEVER render `node-version: ""` or `node-version: "None"`; deploy variants (`deploy-*.yml`) SHALL use the same resolution. A non-empty project `engines.node` SHALL be honored (defaults never override real values). R1 SHALL NOT overwrite a non-empty stored value with an empty discovery result.

#### Scenario: Missing keys fall through to defaults

- GIVEN state with no `discovery.node_engine`/`discovery.npm_major` keys
- WHEN the builder renders `quality-guard.yml`
- THEN `{{node_version}}`→`22`, `{{npm_major}}`→`10`
- AND output contains `node-version: "22"` and `npm install -g npm@10`

#### Scenario: Empty string and null render defaults

- GIVEN `discovery.node_engine`/`discovery.npm_major` are `""` or `null`
- WHEN the builder renders `quality-guard.yml`
- THEN output contains `node-version: "22"` and `npm@10`, never `node-version: ""` or `"None"`

#### Scenario: Literal "None" self-heals

- GIVEN state persisted with `discovery.node_engine = "None"`
- WHEN the builder renders `quality-guard.yml`
- THEN output contains `node-version: "22"`, never the `"None"` string

#### Scenario: Real engines.node is honored

- GIVEN `package.json` `engines.node = "20.x"` stored in state
- WHEN the builder renders `quality-guard.yml` and `deploy.yml`
- THEN both workflows contain `node-version: "20.x"`, not `22`

#### Scenario: Deploy variant shares the resolution

- GIVEN `cd` enabled with node assets but empty `discovery.node_engine`
- WHEN the builder renders the deploy workflow
- THEN `{{node_version}}` resolves to `22` (identical coalescing to quality-guard)

#### Scenario: R1 never clobbers a good value with empty

- GIVEN staging state holds `node_engine = "20.x"` and `package.json` has no `engines.node`
- WHEN R1 re-discovers and drift is accepted
- THEN staging state keeps `"20.x"` (empty discovery result skipped)

### Requirement: FU2 — Commands always re-detected

R1 SHALL re-detect the full script list from `package.json` on EVERY refresh when the manifest exists — never gated on the state value being empty. `OLD_COMMANDS` SHALL be fallback only (no `package.json`/`jq`). The drift gate SHALL fire when the fresh list differs from stored `discovery.commands`; accepted drift SHALL write to staging state.

#### Scenario: Stale partial list is replaced

- GIVEN state holds a stale 4-script list and `package.json` defines 12 scripts
- WHEN R1 re-detects
- THEN the full 12-script list is produced
- AND the drift gate fires (`Commands: <old> → <new>`)
- AND accepting the drift writes the fresh list to staging state

#### Scenario: No package.json falls back to stored list

- GIVEN no `package.json` in the project
- WHEN R1 runs
- THEN `discovery.commands` keeps `OLD_COMMANDS`; no command drift reported

#### Scenario: Scripts removed fire the gate

- GIVEN state lists 5 scripts but `package.json` defines 3
- WHEN R1 re-detects
- THEN the drift gate fires; accepted drift records the 3-script list

#### Scenario: Identical list is a no-op

- GIVEN fresh detection equals the stored list
- WHEN R1 runs
- THEN no command drift is reported and `discovery.commands` is not rewritten

### Requirement: FU3a — Commands rendered as merged bullets

The Commands section SHALL render as a bulleted list with shape `` - `npm run <name>` — <description> `` (backticked). Scripts in `package.json` but new to the current AGENTS.md Commands section SHALL appear without a description; documented scripts SHALL keep descriptions parsed from the current AGENTS.md Commands section (name-keyed merge). The parser SHALL strip backticks before matching and SHALL allow `:` inside script names (canonical npm scripts like `test:e2e`). R1 SHALL report the honest merged/total description count instead of an unconditional success message.

#### Scenario: Backticked rich format round-trips

- GIVEN AGENTS.md Commands has `` - `npm run dev` — Start development server ``
- WHEN AGENTS.md is regenerated and `dev` still exists in `package.json`
- THEN the section contains `` - `npm run dev` — Start development server `` with the description preserved

#### Scenario: Known scripts keep descriptions, new scripts do not

- GIVEN AGENTS.md Commands has `- npm run dev — dev server` and `package.json` adds a `lint` script
- WHEN AGENTS.md is regenerated
- THEN the section contains `- \`npm run dev\` — dev server` and `- \`npm run lint\`` (no description)
- AND no `package.json` script is dropped

#### Scenario: Colon-bearing scripts keep descriptions

- GIVEN AGENTS.md Commands has `` - `npm run test:e2e` — Run E2E tests ``
- WHEN AGENTS.md is regenerated
- THEN the description survives on the `test:e2e` bullet

#### Scenario: No prior section renders description-less bullets

- GIVEN no prior AGENTS.md Commands section (or none with descriptions)
- WHEN AGENTS.md is regenerated
- THEN every script renders as `` - `npm run <name>` `` with an empty description
- AND R1 logs a warning that zero descriptions matched (never a false success)

#### Scenario: Removed scripts disappear

- GIVEN a script documented in AGENTS.md but removed from `package.json`
- WHEN AGENTS.md is regenerated
- THEN that bullet is absent from the Commands section

### Requirement: FU3b — Code Style composed from structured conventions

The Code Style & Conventions section SHALL be re-composed as bullets from `discovery.conventions.{naming,components,imports,tests,css,state}` when any of those fields are present. When none are present, the current AGENTS.md Code Style section SHALL be preserved verbatim (never replaced by the flat `camelCase` placeholder).

#### Scenario: Structured conventions compose bullets

- GIVEN `discovery.conventions` carries `naming: kebab-case` and `tests: vitest`
- WHEN AGENTS.md is regenerated
- THEN Code Style renders bullets from those values, not the `camelCase` fallback

#### Scenario: Absent conventions preserve the existing section

- GIVEN no `discovery.conventions.*` values and a rich AGENTS.md Code Style section
- WHEN AGENTS.md is regenerated
- THEN the existing section content is preserved

### Requirement: FU3c — Project Structure regenerated from the live tree

The Project Structure section SHALL be regenerated from a live filesystem scan performed by R1. Comments from the old section SHALL be preserved where the referenced path/name still matches the live tree; tree-drawing glyphs (`│`, `├`, `└`, `─`) SHALL be normalized before matching so comments survive from tree-formatted sections. A **downgrade guard** SHALL prevent trading a richer section for a poorer one: a fenced or tree-formatted original section SHALL be preserved verbatim, and when regeneration would drop every inline comment the original had, the original section SHALL be kept with a warning.

#### Scenario: New files appear in the tree

- GIVEN a new `src/lib/x.ts` on disk and the old section does not list it
- WHEN AGENTS.md is regenerated
- THEN the tree includes `src/lib/x.ts`

#### Scenario: Matching comments survive

- GIVEN the old section carries `templates/ — single source of truth` and `templates/` still exists
- WHEN AGENTS.md is regenerated
- THEN that comment is preserved on the `templates/` line

#### Scenario: Tree-formatted section survives verbatim

- GIVEN the old section is a fenced code block using box-drawing glyphs (`├── src/  # components`) written by `/wf-init` discovery
- WHEN AGENTS.md is regenerated
- THEN the fenced tree is preserved verbatim (never flattened to a dirs-only list)

#### Scenario: Regeneration losing all comments falls back to the original

- GIVEN a flat old section where every entry carries an inline comment
- AND the regenerated merge matches no comment
- WHEN AGENTS.md is regenerated
- THEN the original section content wins and R1 logs a warning

### Requirement: FU3d — MCP table re-detected and rendered with 3 columns

R1 SHALL re-detect MCPs from known config files (`.mcp.json`, `.cursor/mcp.json`, `.windsurf/mcp.json`, and the documented per-IDE set). The `## Project MCPs` section SHALL render the canonical `| MCP | Purpose | Required setup |` table when purpose/setup are known (detected or merged); otherwise it SHALL fall back to the 2-column `| MCP | Active |` shape. Purpose/Required-setup SHALL merge from the current AGENTS.md table (name-keyed) so a refresh never drops documented setup steps.

#### Scenario: Rich 3-column table survives a round-trip

- GIVEN AGENTS.md carries `| Playwright | Browser control for E2E | npx playwright install --with-deps chromium |`
- WHEN AGENTS.md is regenerated with the same MCP still detected
- THEN the regenerated table keeps Purpose and Required setup intact

#### Scenario: Unknown MCP without prior docs renders 2-column

- GIVEN a detected MCP with no known purpose/setup and no AGENTS.md entry
- WHEN AGENTS.md is regenerated
- THEN it renders as `| MCP | Active |` with `yes` (no fabricated Purpose cells)

#### Scenario: Newly detected MCP appends without dropping rows

- GIVEN a new MCP config appears and an existing MCP is still detected
- WHEN AGENTS.md is regenerated
- THEN the table contains both, preserving the existing row's Purpose/Required setup

### Requirement: FU3e — Preservation is a fallback, not a gate

Section preservation SHALL operate as a FALLBACK only: richer existing content wins over flat state values, but regenerated content SHALL supersede stale preserved text. A stale or partial preserved value SHALL NOT block regeneration of a freshly detectable field (replaces the "backfill only when empty" guard).

#### Scenario: Fresh detection supersedes stale preserved text

- GIVEN staging state carries a stale preserved `discovery.commands` blob that no longer matches `package.json`
- WHEN AGENTS.md is regenerated
- THEN the Commands section reflects the fresh `package.json` scripts, not the stale blob

#### Scenario: Richer existing content wins over flat state

- GIVEN state holds a flat value for a section and AGENTS.md holds a richer multi-line version
- WHEN AGENTS.md is regenerated
- THEN the richer content is used as the merge source and preserved

### Requirement: R4G — Placeholder gate with narrow sed-context exemption

Before diffing, R4 SHALL fail loudly when any wizard-owned placeholder namespace (`{{answers.*}}`, `{{discovery.*}}`, `{{features.*}}`, `{{testing.*}}`, `{{mcps.*}}`, `{{protocols.*}}`, `{{conventions.*}}`, `{{stack.*}}`, `{{wizard_version}}`, `{{version}}`, `{{PROTOCOL_BODY:*}}`) appears unresolved in staging. Arbitrary `{{ }}` text quoted in project docs (e.g. Vue/Angular interpolation) SHALL NOT be flagged. `{{sdd.backend}}` SHALL be exempt ONLY when it appears as a sed search pattern (the runtime literal wf-settings uses to re-resolve the SDD backend post-build, shipped verbatim by builder-core.py by design); occurrences outside that sed-command context SHALL still fail the gate. The exemption scan SHALL use POSIX ERE (`grep -E`) with escaped braces, because BSD grep (macOS) gives undefined behavior for unescaped `{{` in BRE.

#### Scenario: Intentional sed literals do not block the refresh

- GIVEN staging contains the shipped wf-settings skill whose body includes `sed -i.bak "s|{{sdd.backend}}/changes/<name>/proposal.md|$SDD_PROPOSAL_PATH|g"` and `sed -i.bak "s/{{sdd.backend}}/$SDD_BACKEND_PATH/g"`
- WHEN R4 runs the placeholder gate
- THEN the gate passes and the refresh proceeds to the diff step

#### Scenario: Unresolved sdd.backend outside sed context still fails

- GIVEN staging contains a final artifact with prose text `backend is {{sdd.backend}} here`
- WHEN R4 runs the placeholder gate
- THEN the gate fails listing that occurrence and exits non-zero before diffing

#### Scenario: Real leaks are still caught

- GIVEN staging contains an artifact with an unresolved `{{version}}`
- WHEN R4 runs the placeholder gate
- THEN the gate fails regardless of any other content in the same run

### Requirement: FU4 — Deprecated-path cleanup covers per-IDE skills

R4's `DEPRECATED_PATHS` SHALL include per-IDE **skills** paths for the deprecated commands `wf-cicd`, `wf-cleanup`, `wf-refresh`, `wf-init`, `wf-sdd-config`, and the archived `wf-sdd-lite`, across `.claude/skills/`, `.cursor/skills/`, `.opencode/skills/`, `.windsurf/skills/`, `.codex/skills/`, `.kiro/skills/`, `.github/skills/`, and `.devin/skills/`. Such paths SHALL be classified `deleted` only when present on disk AND absent from staging. Deduplication (`unique_by(.path)`) and the R5 approval gate for deletions SHALL be preserved.

#### Scenario: Orphan per-IDE skill is cleaned

- GIVEN `.claude/skills/wf-init/SKILL.md` exists on disk and is not in staging
- WHEN R4 runs
- THEN it is classified `deleted` (reason `deprecated command`)
- AND it appears in the R5 DELETED block requiring approval

#### Scenario: Path in both baseline and DEPRECATED_PATHS counts once

- GIVEN a path appears in the managed_paths baseline and in `DEPRECATED_PATHS`
- WHEN R4 runs
- THEN deduplication yields a single `deleted` entry

#### Scenario: Still-current skill is never deleted

- GIVEN a per-IDE skills path that exists in staging (still part of the build)
- WHEN R4 runs
- THEN it is NOT classified `deleted` even if listed in `DEPRECATED_PATHS`

### Requirement: FU5 — Non-tty robustness with structured manifest and resume

A non-tty run with an unanswered prompt (no `WF_REFRESH_ANSWERS` entry, no `WF_REFRESH_DEFAULT_ANSWER`) SHALL NOT abort the pipeline with a bare `exit 2`. It SHALL emit a structured pending-prompts manifest (`GENTLE_AI_WF_REFRESH_NEEDS="prompt=...|..."` payload), exit with a clear documented code, and either clean `.wizard-staging/`/`refresh-plan.json`/baseline or print exact resume instructions.

Pre-R5 prompts (R1 drift, R2 features) SHALL stop their owning phase IMMEDIATELY via fail-fast (`_require_answer_or_stop`): continuing on a default answer would build staging from stale info, and an answer collected later would have no consumer because the owning phase never re-runs. The failing phase SHALL write `.wizard-resume-phase` before exiting 3. With `WF_REFRESH_RESUME=1`, phases R-1→R4 SHALL consult that marker: phases before the target skip themselves, the target phase consumes the marker and re-runs fully (its prompts resolve from `WF_REFRESH_ANSWERS`), and the pipeline continues through R5 normally. Without a marker, `WF_REFRESH_RESUME=1` SHALL preserve the legacy behavior of skipping R-1→R4 and re-entering the R5 gate with staging intact (for runs stopped at R5). Abort paths (R5 cancel, apply-gate refusal) SHALL clean staging/plan or print exact resume steps.

#### Scenario: Unanswered pre-R5 prompt stops its phase

- GIVEN a non-tty run and the R1 drift prompt has no answer and no default
- WHEN `_require_answer_or_stop` is called
- THEN the phase stops immediately (before any staging work) instead of taking a silent default-"no" path
- AND it prints `GENTLE_AI_WF_REFRESH_NEEDS="prompt=..."` with exit code 3
- AND `.wizard-resume-phase` names the phase that asked
- AND no orphaned `.wizard-staging/`, `refresh-plan.json`, or `.wizard-refresh-baseline.json` remain (or exact resume instructions are printed)

#### Scenario: Resume re-enters the phase that recorded the prompt

- GIVEN a previous non-tty run stopped at R1 or R2 with `.wizard-resume-phase` written
- WHEN re-run with `WF_REFRESH_RESUME=1` and the matching `WF_REFRESH_ANSWERS` entry
- THEN earlier phases skip themselves via the marker
- AND the marked phase re-runs fully, consuming the supplied answer
- AND the pipeline continues through R3→R5 normally

#### Scenario: Resume re-enters R5 with staging intact

- GIVEN a previous run stopped at the R5 gate and `.wizard-staging/` + `refresh-plan.json` still exist, with no `.wizard-resume-phase` marker
- WHEN re-run with `WF_REFRESH_RESUME=1`
- THEN R-1→R4 are skipped
- AND the R5 review gate re-enters with the preserved plan and staging intact

#### Scenario: Supplied answers avoid the manifest

- GIVEN `WF_REFRESH_ANSWERS="Use updated project info?=yes"` in a non-tty run
- WHEN the matching prompt is asked
- THEN the answer is consumed normally and no manifest is emitted

#### Scenario: Apply-gate refusal is resumable

- GIVEN a non-tty run at the R5 apply gate with `WF_REFRESH_APPLY_MODE` unset
- WHEN the gate cannot decide
- THEN it emits the pending-prompts manifest instead of a generic abort
- AND staging/plan are preserved for a `WF_REFRESH_RESUME=1` re-entry (or cleaned with resume steps printed)

### Requirement: FU6 — Apply-only deletions are never staged

In apply-only mode, approved `deleted`/`deleted_modified` files SHALL be removed with plain `rm -f` (unstaged, uniform with the `cp` of edits). `git rm` SHALL be used only in commit mode. The R6 closing message SHALL be accurate in apply-only mode (changes left in the working tree, unstaged — including deletions).

#### Scenario: Apply-only deletions are unstaged

- GIVEN apply-only mode and approved `deleted` entries
- WHEN R6 applies
- THEN the files are removed from the working tree with plain `rm`
- AND `git status` shows the deletions as unstaged
- AND the closing message states changes were left unstaged

#### Scenario: Commit mode stages deletions

- GIVEN commit mode and approved `deleted` entries
- WHEN R6 applies
- THEN `git rm` stages the deletions and the commit contains them

#### Scenario: Apply-only with no deletions is unchanged

- GIVEN apply-only mode with zero deletions
- WHEN R6 applies
- THEN no git operation runs and the closing message is accurate

#### Scenario: deleted_modified also uses plain rm in apply-only

- GIVEN apply-only mode and approved `deleted_modified` entries
- WHEN R6 applies
- THEN those files are removed with plain `rm -f`, unstaged

### Requirement: FU7 — Locally-modified `updated` files are protected

R4 SHALL mark `updated` entries with `local_modified: true` when the working-tree file differs from HEAD (fallback: recorded `generated_files` hash; non-git projects without a recorded hash SHALL treat the file as plain `updated`). R5 SHALL list them in a dedicated warning block and ask a dedicated approval (`Overwrite locally-modified files?`). R6 SHALL overwrite them only when that approval is true. The `refresh-plan.json` schema change (new `local_modified` field) SHALL land in the same change, with R5/R6 consumers updated in lockstep.

#### Scenario: Local edits flag and gate the file

- GIVEN an `updated` file whose working-tree content differs from HEAD
- WHEN R4 classifies it
- THEN the plan entry carries `local_modified: true`
- AND R5 shows it in a dedicated warning block with the `Overwrite locally-modified files?` approval

#### Scenario: Overwrite declined keeps the local file

- GIVEN the dedicated overwrite approval is `no`
- WHEN R6 applies updates
- THEN the locally-modified file is NOT overwritten
- AND other approved files are still applied

#### Scenario: Overwrite approved replaces the file

- GIVEN the dedicated overwrite approval is `yes`
- WHEN R6 applies updates
- THEN the file is overwritten with the staged version

#### Scenario: Clean updated file skips the extra gate

- GIVEN an `updated` file identical to HEAD
- WHEN R4 classifies it
- THEN it has no `local_modified` flag and only the normal updated approval applies

#### Scenario: Non-git fallback

- GIVEN a non-git project where the working-tree file matches the recorded `generated_files` hash (or no hash is recorded)
- WHEN R4 classifies it
- THEN it is treated as plain `updated` without the local-modified gate

---

## Capability: `state-migration`

### Requirement: R2 — Normalize corrupted node/npm discovery values

The R2 migration SHALL normalize `discovery.node_engine` and `discovery.npm_major` values of literal `"None"` or `""` to `null`/absent, so the builder defaults (`"22"`/`"10"`) apply. Valid values SHALL be preserved unchanged. Normalization SHALL run unconditionally and idempotently alongside the existing legacy normalization block (even when versions match), and SHALL operate on the staging state copy.

#### Scenario: Literal "None" normalizes to absent

- GIVEN staging state holds `discovery.node_engine = "None"` and `discovery.npm_major = "None"`
- WHEN R2 migration runs
- THEN both values become `null`/absent
- AND the builder renders `node-version: "22"` / `npm@10`

#### Scenario: Empty strings normalize to absent

- GIVEN staging state holds `discovery.node_engine = ""` and `discovery.npm_major = ""`
- WHEN R2 migration runs
- THEN both values become `null`/absent and builder defaults apply

#### Scenario: Valid values are preserved

- GIVEN staging state holds `discovery.node_engine = "20.x"` and `discovery.npm_major = "10"`
- WHEN R2 migration runs
- THEN both values are untouched

#### Scenario: Normalization is idempotent

- GIVEN state already normalized (values `null`/absent)
- WHEN R2 migration runs again
- THEN the state is unchanged (no-op)

---

## Change-wide requirements

### Requirement: DOC-SYNC — AI_DEV_WORKFLOW.md updated in the same change

`AI_DEV_WORKFLOW.md` sections covering R1/R4/R5/R6 (~709, 762, 765-767, 1699-1710) SHALL be updated in the same change, reflecting the new regeneration-first merge, coalesced defaults, extended `DEPRECATED_PATHS`, non-tty manifest/resume, apply-only deletion semantics, and the `local_modified` gate. The AGENTS.md sync rule SHALL hold: no code change commits without the doc audit.

#### Scenario: Doc mirrors code behavior

- GIVEN code changes for FU1–FU7/R2 are implemented
- WHEN the change is committed
- THEN AI_DEV_WORKFLOW.md R1/R4/R5/R6 sections describe the new behavior (and line ~765 no longer overstates `DEPRECATED_PATHS` coverage)

#### Scenario: Doc-only change is not committed alone

- GIVEN a doc edit with no matching code change
- WHEN the review gate runs
- THEN the change is flagged incomplete (doc sync is part of this change, not standalone)

---

## Verification notes

No test runner exists (markdown repo, strict TDD false). Verification per proposal success criteria: `python3 -m py_compile` on `builder-core.py`/`builder-heavy.py`; `bash -n` on every modified refresher block; fixture dry-runs (a) no `engines.node` + corrupt state self-heal, (b) stale partial commands replaced by merged bullets, (c) rich 3-column MCPs table survives round-trip, (d) apply-only deletions unstaged + truthful closing message, (e) locally-modified `updated` file flagged and gated; non-tty manifest/resume check; `DEPRECATED_PATHS` coverage check against `meta.md`/`install.sh`.