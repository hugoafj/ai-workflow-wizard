# Tasks: Fix `/wf-refresh` field-report defects (FU1–FU7)

**Change**: `fix-wf-refresh-field-report`  
**Status**: Tasks  
**Created**: 2026-08-20

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 550–750 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (FU1, FU2, FU3a, FU3b) → PR 2 (FU3c, FU3d, FU3e, FU4) → PR 3 (FU5, FU6, FU7, R2, Doc-sync) |
| Delivery strategy | single-pr |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| WU-1 | Coalesce empty/node_engine defaults in builder | PR 1 | `python3 -m py_compile wf-init/lib/builder-core.py && python3 -m py_compile wf-init/lib/builder-heavy.py` | Dry-run builder on temp project with empty node_engine | Revert builder-core.py/builder-heavy.py |
| WU-2 | R1 always re-detects commands from package.json | PR 1 | `bash -n wf-init/lib/refresher.md` (R1 block) | Fixture: stale 4 scripts vs 12 in package.json → drift fires | Revert refresher.md R1 commands block |
| WU-3 | Commands bullets + Code Style compose from conventions | PR 1 | `bash -n wf-init/lib/refresher.md` (R1 merge) + py_compile | Dry-run: AGENTS.md Commands + conventions → bullets rendered | Revert refresher.md R1 merge + builder-core infer_placeholder |
| WU-4 | Structure from live tree + MCPs 3-col table | PR 2 | `bash -n wf-init/lib/refresher.md` (R1 structure/MCPs) + py_compile | Dry-run: nested tree + 3-col MCP table survives round-trip | Revert refresher.md R1 structure/MCPs + builder-core mcps.table |
| WU-5 | DEPRECATED_PATHS extended with per-IDE skills | PR 2 | `bash -n wf-init/lib/refresher.md` (R4 DEPRECATED_PATHS) | Dry-run: orphan per-IDE skills of 6 deprecated commands listed for deletion | Revert refresher.md R4 DEPRECATED_PATHS array |
| WU-6 | Non-tty manifest + resume protocol | PR 3 | `bash -n wf-init/lib/refresh-lib.sh` (embedded) + `bash -n refresher.md` (R5) | Non-tty run with missing answers → manifest + exit 3; RESUME=1 re-enters R5 | Revert refresh-lib.sh _ask_yesno_safe + refresher.md R5 manifest/resume |
| WU-7 | Apply-only plain rm (no git staging) | PR 3 | `bash -n wf-init/lib/refresher.md` (R6 apply block) | Apply-only dry-run → git status shows deletions unstaged | Revert refresher.md R6 apply block |
| WU-8 | local_modified flag + dedicated overwrite approval | PR 3 | `bash -n wf-init/lib/refresher.md` (R4/R5/R6 local_modified) | Dry-run with uncommitted AGENTS.md → warning + prompt → overwrite only on yes | Revert refresher.md R4/R5/R6 local_modified logic |
| WU-9 | R2 normalization of "None"/"" → null | PR 3 | `bash -n wf-init/lib/refresher.md` (R2 migrate block) | Dry-run with corrupted state → normalizes on next refresh | Revert refresher.md R2 normalize block |
| WU-10 | AI_DEV_WORKFLOW.md doc-sync (inline per WU) | Each PR | Manual review of affected sections | N/A (doc audit) | Revert AI_DEV_WORKFLOW.md sections touched |

---

## Phase 1: Foundation — Coalescing + Commands Re-detection (WU-1, WU-2)

### WU-1: FU1 — node_version/npm_major coalescing (builder-core.py only)

- [ ] 1.1 Add `_coalesce(state, path, default)` helper in `wf-init/lib/builder-core.py` (near `get_state_value`)
- [ ] 1.2 Update quality-guard placeholder resolution (~line 301) to use `_coalesce(state, "discovery.node_engine", "22")` and `_coalesce(state, "discovery.npm_major", "10")`
- [ ] 1.3 Update deploy workflow placeholder resolution (~line 490) to use same `_coalesce` calls
- [ ] 1.4 Ensure R1 drift write in refresher.md skips empty discovery results for node_engine/npm_major (preserves existing good values)
- [ ] 1.5 Run `python3 -m py_compile wf-init/lib/builder-core.py && python3 -m py_compile wf-init/lib/builder-heavy.py`
- [ ] 1.6 Dry-run: create temp project without engines.node, corrupt state with empty strings, run builder-heavy → verify quality-guard.yml shows `node-version: "22"` and `npm@10`

### WU-2: FU2 — Commands always re-detected (refresher.md R1 only)

- [ ] 2.1 Locate R1 commands detection block (~lines 723-730) in `wf-init/lib/refresher.md`
- [ ] 2.2 Rewrite to always run `jq -r '.scripts | keys[]' package.json` when package.json exists (remove empty-state gate)
- [ ] 2.3 Keep `OLD_COMMANDS` fallback only when no package.json or jq fails
- [ ] 2.4 Ensure drift gate fires when fresh list differs from stored `discovery.commands`
- [ ] 2.5 Run `bash -n wf-init/lib/refresher.md`
- [ ] 2.6 Dry-run: fixture with state holding 4 scripts, package.json with 12 → drift reported, accepted drift writes fresh list

---

## Phase 2: Regeneration-First Merge — Commands/Code Style/Structure/MCPs (WU-3, WU-4)

### WU-3: FU3a+b — Commands bullets + Code Style compose (refresher.md R1 + builder-core.py)

- [ ] 3.1 In R1 (refresher.md ~770-836): parse current AGENTS.md Commands section into `name -> description` map using `_wf_section` or equivalent
- [ ] 3.2 Emit merged bullets: `- npm run <name> — <description>` (description empty for new scripts); write to `discovery.commands` in state
- [ ] 3.3 In `builder-core.py` `infer_placeholder` (~472-477): add `discovery.conventions.code_style` composition from `discovery.conventions.{naming,components,imports,tests,css,state}`
- [ ] 3.4 Format: `- Naming: <value>`, `- Components: <value>`, etc.; only include fields that are present
- [ ] 3.5 Fallback: preserve current AGENTS.md Code Style section verbatim when ALL structured fields absent
- [ ] 3.6 Run `bash -n wf-init/lib/refresher.md` + `python3 -m py_compile wf-init/lib/builder-core.py`
- [ ] 3.7 Dry-run: builder renders bullets with descriptions; code_style shows all 6 fields when populated

### WU-4: FU3c+d — Structure from live tree + MCPs 3-col (refresher.md R1 + builder-core.py)

- [ ] 4.1 In R1: regenerate structure tree via `find` (depth 2, exclude `node_modules/.git/dist/.wizard-*`)
- [ ] 4.2 Parse old AGENTS.md `## Project Structure` section; merge comments by exact path-name match; new paths render without comment
- [ ] 4.3 Write merged structure to `discovery.conventions.structure`
- [ ] 4.4 In R1: re-detect MCPs from known configs (`.mcp.json`, `.cursor/mcp.json`, `.windsurf/mcp.json`, `.github/copilot-instructions.md` hints)
- [ ] 4.5 Parse old AGENTS.md MCP table (3-col `| MCP | Purpose | Required setup |`); merge purpose/setup by MCP name
- [ ] 4.6 Extend `state.mcps[]` entries with optional `purpose`/`setup` fields (schema-compatible)
- [ ] 4.7 In `builder-core.py` `infer_placeholder("mcps.table")` (~497-512): render 3-col when `purpose` present, else 2-col fallback
- [ ] 4.8 Run `bash -n wf-init/lib/refresher.md` + `python3 -m py_compile wf-init/lib/builder-core.py`
- [ ] 4.9 Dry-run: test project with nested structure + 3-col MCP table → round-trip preserves Purpose/Required-setup

---

## Phase 3: Safety Completions — Deprecated Paths, Non-tty, Apply-only, Local-modified (WU-5, WU-6, WU-7, WU-8)

### WU-5: FU4 — DEPRECATED_PATHS per-IDE skills (refresher.md R4)

- [ ] 5.1 Extend R4 `DEPRECATED_PATHS` array with per-IDE skill dirs for 6 deprecated commands: `wf-cicd`, `wf-cleanup`, `wf-refresh`, `wf-init`, `wf-sdd-config`, `wf-sdd-lite`
- [ ] 5.2 Cover 8 IDE roots: `.claude/skills/`, `.cursor/skills/`, `.opencode/skills/`, `.windsurf/skills/`, `.codex/skills/`, `.kiro/skills/`, `.github/skills/`, `.devin/skills/`
- [ ] 5.3 `.devin` only when windsurf active (check `reinsert_legacy_bridge` logic)
- [ ] 5.4 Guard: classify as `deleted` only when present on disk AND absent from staging; dedup via `unique_by(.path)`; R5 approval gate preserved
- [ ] 5.5 Run `bash -n wf-init/lib/refresher.md`
- [ ] 5.6 Dry-run: project with orphan per-IDE skills of deprecated commands → all listed for deletion in R5

### WU-6: FU5 — Non-tty manifest + resume (state-helpers.sh _ask_yesno_safe + refresher.md R5)

- [ ] 6.1 In `wf-init/lib/state-helpers.sh` (embedded in refresher.md): modify `_ask_yesno_safe` to record pending prompt in global array instead of `exit 2`; return sentinel value
- [ ] 6.2 In R5 (refresher.md): before any approval gate, collect ALL pending prompts from R-1/R1/R2/R5 phases
- [ ] 6.3 Emit `GENTLE_AI_WF_REFRESH_NEEDS="prompt=<p1>|prompt=<p2>|...|apply_mode=..."` with exit code 3
- [ ] 6.4 Implement `WF_REFRESH_RESUME=1`: skip R-1..R4 (validate staging/plan exist); re-enter R5 with staging intact
- [ ] 6.5 Abort paths (R-1/R1/R2/R4): clean staging/plan or print exact resume instructions
- [ ] 6.6 Run `bash -n wf-init/lib/refresh-lib.sh` (extracted) + `bash -n wf-init/lib/refresher.md` (R5 block)
- [ ] 6.7 Dry-run: non-tty with missing `WF_REFRESH_ANSWERS` → emits manifest + exit 3; resume works with staging intact

### WU-7: FU6 — Apply-only plain rm (refresher.md R6)

- [ ] 7.1 In R6 (~1498, 1509): use `rm -f` when `APPLY_ONLY == true`; `git rm -f` only in commit mode
- [ ] 7.2 Correct closing message (~1686): "changes left in the working tree (unstaged)" for all categories
- [ ] 7.3 Run `bash -n wf-init/lib/refresher.md` (R6 block)
- [ ] 7.4 Dry-run: apply-only with approved deletions → `git status` shows deletions unstaged; closing message accurate

### WU-8: FU7 — Local-modified flag + overwrite approval (refresher.md R4/R5/R6)

- [ ] 8.1 In R4 (~1078-1087): mark `updated` entries with `local_modified: true` when `git diff --quiet HEAD -- <file>` fails
- [ ] 8.2 Fallback: compare against recorded `old_hash` when no HEAD (non-git projects)
- [ ] 8.3 In R5: dedicated warning block listing locally-modified files; dedicated approval `Overwrite locally-modified files?` → stored as `build_plan.approval.overwrite_local`
- [ ] 8.4 In R6: copy `local_modified` files only when `overwrite_local` approval is true
- [ ] 8.5 Update `refresh-plan.json` schema: `updated[]` gains `local_modified: boolean` (default false, backwards-compatible)
- [ ] 8.6 Run `bash -n wf-init/lib/refresher.md` (R4/R5/R6 blocks)
- [ ] 8.7 Dry-run: AGENTS.md with uncommitted changes → flagged, warning block shown, overwrite only on yes

---

## Phase 4: Migration + Doc-sync (WU-9, WU-10)

### WU-9: R2 Normalization (refresher.md R2 / migrate_state)

- [ ] 9.1 In R2 migration block: add idempotent jq to normalize `discovery.node_engine` and `discovery.npm_major` from `"None"`/`""` to `null`/absent
- [ ] 9.2 Preserve valid values unchanged; run unconditionally alongside existing legacy normalization
- [ ] 9.3 Operate on staging state copy
- [ ] 9.4 Run `bash -n wf-init/lib/refresher.md` (R2 block)
- [ ] 9.5 Dry-run: corrupted state with `"None"`/`""` → normalizes on next refresh; builder defaults apply

### WU-10: Doc-sync AI_DEV_WORKFLOW.md (inline with WU-2 through WU-8)

- [ ] 10.1 Update R1 section (~line 709) to document regeneration-first merge for commands/structure/MCPs
- [ ] 10.2 Update R4 section (~line 762, 765-767) to reflect extended DEPRECATED_PATHS and local_modified classification
- [ ] 10.3 Update R5/R6 sections (~line 767) to document non-tty manifest/resume, overwrite_local approval, apply-only semantics
- [ ] 10.4 Update MCP table canonical shape (~1699-1710) to match 3-column renderer
- [ ] 10.5 Verify no code change committed without doc audit (AGENTS.md sync rule)
- [ ] 10.6 Manual review: doc mirrors code behavior for all FU1–FU7/R2 changes

---

## Implementation Order

**Recommended sequence** (respects dependencies and safe incremental delivery):

1. **WU-1** (FU1 coalescing) — lowest risk, builder-only, enables all downstream rendering
2. **WU-2** (FU2 commands re-detect) — R1 only, no builder changes
3. **WU-3** (FU3a+b commands bullets + code_style) — depends on WU-2 R1 changes, adds builder compose
4. **WU-4** (FU3c+d structure + MCPs 3-col) — depends on WU-3 R1 merge pattern, adds builder mcps.table
5. **WU-5** (FU4 DEPRECATED_PATHS) — independent R4 extension
6. **WU-6** (FU5 non-tty manifest+resume) — state-helpers.sh + R5, independent
7. **WU-7** (FU6 apply-only rm) — R6 only, independent
8. **WU-8** (FU7 local_modified) — touches R4/R5/R6, depends on WU-6 R5 manifest pattern
9. **WU-9** (R2 normalization) — independent R2 addition
10. **WU-10** (Doc-sync) — inline with each WU above; final pass to verify all sections updated

**Checkpoints** (user review gates):
- After WU-1, WU-2, WU-3: Phase 1+2 complete (regeneration-first core)
- After WU-4, WU-5: Phase 3 complete (structure/MCPs + deprecated paths)
- After WU-6, WU-7, WU-8: Phase 4 complete (safety completions)
- After WU-9, WU-10: Phase 5 complete (migration + docs)

---

## Risk Mitigation

| Risk | Task-Level Mitigation |
|------|----------------------|
| Merge overwrites user AGENTS.md | WU-3/WU-4: "richer content wins" merge logic; R5 diff preview is safety net |
| FU4 deletes project skills | WU-5: guard "present on disk AND absent from staging" + R5 approval gate |
| FU7 schema change breaks mid-run | WU-8: R5/R6 consumers updated in same WU; schema backwards-compatible |
| PR exceeds 400 lines | Chained PR split (3 PRs); each WU is independently revertible |
| Non-tty contract breaks consumers | WU-6: fixed format documented in AI_DEV_WORKFLOW.md |

---

## Success Criteria (per proposal)

- [ ] `python3 -m py_compile` passes on `builder-core.py`/`builder-heavy.py`
- [ ] `bash -n` passes on every modified refresher block
- [ ] Fixture (a): no `engines.node` + corrupt state self-heals → `node-version: "22"` / `npm@10`
- [ ] Fixture (b): stale partial commands replaced by full fresh list as merged bullets
- [ ] Fixture (c): rich 3-column MCPs table survives round-trip (Purpose/Required-setup preserved)
- [ ] Fixture (d): apply-only deletions unstaged + truthful closing message
- [ ] Fixture (e): locally-modified `updated` file flagged, listed separately, requires dedicated approval
- [ ] Non-tty manifest emits `GENTLE_AI_WF_REFRESH_NEEDS` + exit 3; `WF_REFRESH_RESUME=1` re-enters R5; no orphaned artifacts
- [ ] `DEPRECATED_PATHS` covers per-IDE skills + `wf-sdd-lite`; `AI_DEV_WORKFLOW.md:765` wording matches
- [ ] `AI_DEV_WORKFLOW.md` R1/R4/R5/R6 sections updated in same change
- [ ] No commits without user review

---

## Next Step

Ready for implementation (`sdd-apply`). The user must confirm the chained PR strategy (feature-branch-chain with 3 PRs) before apply begins, as delivery strategy is `single-pr` but budget risk is Medium.