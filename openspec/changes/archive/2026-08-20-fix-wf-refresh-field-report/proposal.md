# Proposal: Fix `/wf-refresh` field-report defects (FU1–FU7)

**Change**: `fix-wf-refresh-field-report`
**Status**: Proposal
**Created**: 2026-08-20

## Problem statement

The builder-driven `/wf-refresh` pipeline (`wf-init/lib/refresher.md`, `builder-*.py`, `refresh-lib.sh`) ships seven field-report defects verified against the current tree (see `exploration.md`):

1. **FU1 — Empty node version**: `quality-guard.yml` renders `node-version: ""` or `"None"` because `get_state_value` only applies its default when the key is absent; `state.md` declares `null` schema defaults and R1 writes empty strings for projects without `engines.node`. The documented "or 22 by default" contract (`templates/protocols/cicd/variants/quality-guard.yml.md:4-5,36,40`) is unreachable.
2. **FU2 — Stale commands never re-detected**: R1 gates `package.json` script detection on the state value being empty, so an old partial list is written back and the drift gate never fires.
3. **FU3 — Regenerated AGENTS.md flattens rich content**: backfill only runs on empty fields; MCP tables collapse to `{name, active}` end-to-end, losing Purpose/Required-setup documentation (`AI_DEV_WORKFLOW.md:1704` canonical shape).
4. **FU4 — Incomplete deprecated-path cleanup**: per-IDE **skills** dirs (`<ide>/skills/wf-*`) and the archived `wf-sdd-lite` command are missing from `DEPRECATED_PATHS`; `AI_DEV_WORKFLOW.md:765` overstates coverage.
5. **FU5 — Non-tty aborts orphan artifacts**: `_ask_yesno_safe` `exit 2` leaves `.wizard-staging/`, `refresh-plan.json`, `.wizard-refresh-baseline.json` behind with no resume path.
6. **FU6 — Apply-only leaves mixed git state**: deletions are staged (`git rm`) while edits stay unstaged; the closing message is false for deletions.
7. **FU7 — Local edits silently overwritten**: `updated` files with uncommitted local changes are `cp`'d over without warning or approval.

## Objective

Make `/wf-refresh` produce a **complete, correct field report** in AGENTS.md and run **safely in non-interactive contexts**:

- Every refresh reflects the live project (scripts, structure, MCP configs, conventions) with rich merged content, never flattened placeholders.
- Non-tty runs never abort mid-pipeline; pending prompts are surfaced as a structured manifest and resumable.
- Apply-only leaves a working tree free of staged deletions; locally-modified files are never overwritten silently.

## Scope

### In Scope

One consolidated change covering all seven fixes plus one migration normalization:

| # | Fix | Where | Behavior |
|---|-----|-------|----------|
| FU1 | Coalesce empty/`null` → defaults | `builder-core.py` `get_state_value`/new `_coalesce` + `builder-heavy.py:301-302` | `""`/`None`/missing all fall through to `"22"`/`"10"`; R1 drift write skips empty values |
| FU2 | Always re-detect commands | `refresher.md` R1 (~723-730) | Re-detect from `package.json` whenever the manifest exists; `OLD_COMMANDS` is fallback only |
| FU3a | Commands as merged bullets | `refresher.md` R1 (~770-836) + `builder-core.py` | Render `- npm run <name> — <description>`; new scripts get no description, known scripts keep parsed descriptions from current AGENTS.md |
| FU3b | Code Style from structured conventions | `builder-core.py` `infer_placeholder` (~472-477) | Re-compose bullets from `discovery.conventions.{naming,components,imports,tests,css,state}` |
| FU3c | Structure from live filesystem | `refresher.md` R1 | Re-generate tree from filesystem; keep old AGENTS.md comments where names match |
| FU3d | MCP table 3 columns | `builder-core.py` `infer_placeholder("mcps.table")` (~497-512) + R1 backfill | Re-detect known configs (`.mcp.json`, `.cursor/mcp.json`, `.windsurf/mcp.json`, …); preserve Purpose/Required-setup from old AGENTS.md; render `| MCP | Purpose | Required setup |` per `AI_DEV_WORKFLOW.md:1699-1710` |
| FU3e | Preservation as fallback only | `refresher.md` R1 | Current AGENTS.md sections kept only when content is not derivable |
| FU4 | Extend `DEPRECATED_PATHS` | `refresher.md` R4 (~1148-1156) | Add per-IDE skills dirs (`.claude/`, `.cursor/`, `.opencode/`, `.windsurf/`, `.codex/`, `.kiro/`, `.github/`, `.devin/` `/skills/wf-{cicd,cleanup,refresh,init,sdd-config}/SKILL.md`) + archived `wf-sdd-lite`; sync `AI_DEV_WORKFLOW.md:765` |
| FU5 | Non-tty robustness + resume | `refresh-lib.sh` `_ask_yesno_safe` (~217-272) + R5 | No `exit 2` on unanswered prompt: emit `GENTLE_AI_WF_REFRESH_NEEDS="prompt=...|..."` + clear exit code; `WF_REFRESH_RESUME=1` skips R-1→R4 and re-enters R5 with staging intact; clean staging/plan on abort or print exact resume steps |
| FU6 | Apply-only git hygiene | `refresher.md` R6 (~1498,1509) | Plain `rm -f` for deletions in apply-only; `git rm` only in commit mode; fix closing message |
| FU7 | Locally-modified protection | `refresher.md` R4 (~1078-1087) + R5 + R6 | R4 flags `local_modified: true` on `updated` files whose working tree ≠ HEAD; R5 lists them in a separate block with dedicated `Overwrite locally-modified files?` approval; R6 respects it |
| R2 | State normalization | `refresher.md` R2 | Normalize corrupted `discovery.node_engine`/`discovery.npm_major` (`"None"`/`""`) during migration |

### Out of Scope

- New user-facing features beyond `/wf-refresh` correctness.
- Full interactive resume UI / phase progress journaling beyond the `WF_REFRESH_RESUME=1` R5 re-entry.
- Refactoring `/wf-init` builder logic beyond the `get_state_value`/`infer_placeholder` touches above.
- Adding a real test harness (markdown repo, strict TDD false); verification stays `bash -n`, `python3 -m py_compile`, and fixture dry-runs.

## Capabilities

### New Capabilities

None — this is a corrective change to existing behavior.

### Modified Capabilities

- `wf-refresh`: field-report generation becomes regeneration-first with merge (commands/Code Style/structure/MCPs); R4 classification adds `local_modified`; R5 adds non-tty manifest output, resume entry, and overwrite approval; R6 apply-only semantics change; R2 normalizes corrupted discovery values; `DEPRECATED_PATHS` extended.
- `state-migration`: R2 gains normalization of `discovery.node_engine`/`discovery.npm_major` corrupt values.

## Approach

### Regeneration-first with merge (FU2 + FU3)

R1 re-detects all discoverable fields unconditionally (scripts from `package.json`, tree from the live filesystem, MCPs from known config files). The current AGENTS.md is parsed once and used as a **merge source**: descriptions/comments/purpose survive where names match, and rich sections are re-rendered from structured `discovery.*` state instead of being carried as opaque blobs. The old "fill empty fields only" backfill is replaced by this merge; whole-section preservation remains only as the final fallback (FU3e).

### Coalescing at the builder boundary (FU1 + R2)

Harden `get_state_value` (or add `_coalesce`) so `""`/`None`/missing all resolve to the documented defaults; R1 stops writing empty `node_engine`/`npm_major` into state; R2 migration rewrites already-corrupted values.

### Safety completions (FU4–FU7)

FU4 extends the deprecated-path list (loops over IDEs × commands). FU5 moves abort handling to a structured manifest (`GENTLE_AI_WF_REFRESH_NEEDS`) with a resume gate. FU6 splits deletion semantics by mode. FU7 adds the `local_modified` classification with a dedicated approval gate.

### Doc sync (mandatory)

`AI_DEV_WORKFLOW.md` sections R1/R4/R5/R6 (~709, 762, 765-767, 1699-1710) and `templates/protocols/cicd/variants/quality-guard.yml.md` contract notes are updated in the same change (AGENTS.md constraint; no code commit without doc audit).

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `wf-init/lib/refresher.md` | Modified | R1 merge logic (FU2/FU3), R2 normalization, R4 `DEPRECATED_PATHS` + `local_modified`, R5 manifest/resume/overwrite gate, R6 apply-only semantics |
| `wf-init/lib/refresh-lib.sh` (embedded in refresher.md) | Modified | `_ask_yesno_safe` non-tty manifest instead of `exit 2` |
| `wf-init/lib/builder-core.py` | Modified | `get_state_value` coalescing, `mcps.table` 3-column render, Code Style re-composition |
| `wf-init/lib/builder-heavy.py` | Modified | `node_version`/`npm_major` placeholder resolution |
| `wf-init/lib/state.md` | Modified | Schema notes for `node_engine`/`npm_major` defaults + `mcps` columns |
| `templates/protocols/cicd/variants/quality-guard.yml.md` | Modified | Contract wording aligned with coalescing behavior |
| `AI_DEV_WORKFLOW.md` | Modified | R1/R4/R5/R6 documentation sync (~709, 762, 765-767, 1699-1710) |
| `openspec/changes/fix-wf-refresh-field-report/` | New | SDD artifacts (this proposal, then specs/design/tasks) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Merge semantics overwrite user-curated AGENTS.md sections | Medium | Keep "richer content wins" guard; R5 `diff -u` preview remains the safety net; explicit approval required |
| FU4 list expansion deletes intentionally-installed project skills | Medium | Keep "delete only wizard-pattern paths"; R5 approval gate for deletions |
| FU7 changes `refresh-plan.json` schema — mid-run abort if consumers out of sync | Medium | Update R5/R6 consumers and commit path lists in the same change |
| Already-corrupted `"None"`/`""` state values don't self-heal | Low | R2 normalization included in this change (extra scope item) |
| PR exceeds 400 changed lines | Medium | Split into work-unit commits per fix (FU1/FU6 low-risk first) |
| Non-tty manifest contract breaks consumers | Low | Fixed format `GENTLE_AI_WF_REFRESH_NEEDS="prompt=...|..."` documented in `AI_DEV_WORKFLOW.md` |

## Rollback Plan

1. No push until user approval (repo constraint).
2. Each fix lands as its own work-unit commit on a feature branch; revert per-commit with `git revert <commit>` if a defect resurfaces.
3. `/wf-refresh` re-runs from scratch (staging is disposable); `wf-cleanup` + `/wf-init` rebuild project artifacts from a clean state.
4. `WF_REFRESH_KEEP_STAGING`/`--keep` escape hatch retained for diagnostics before any cleanup-trap change.

## Dependencies

- Base: current `main` head of the `fix(wf-refresh)` series (commit `5e8b0e2`).
- **Release note**: fixes ship in the **next local release**; `/wf-refresh` downloads `wf-init/lib/refresher.md` from remote `main`, so consumers pick them up only **after push** — until then, tests must run against the working tree.

## Success Criteria

- [ ] `python3 -m py_compile` passes on `builder-core.py`/`builder-heavy.py`; `bash -n` passes on every modified refresher block.
- [ ] Fixture dry-run (a): project without `engines.node` renders `node-version: "22"` / `npm@10` in `quality-guard.yml`; corrupt `"None"`/`""` state self-heals via R2.
- [ ] Fixture dry-run (b): stale partial commands list is replaced by the full fresh script list rendered as bullets with descriptions merged from AGENTS.md.
- [ ] Fixture dry-run (c): rich 3-column MCPs table survives a refresh round-trip (Purpose/Required-setup preserved).
- [ ] Fixture dry-run (d): apply-only run with deletions leaves working-tree deletions **unstaged** and the closing message truthful.
- [ ] Fixture dry-run (e): an `updated` file with local edits is flagged `local_modified`, listed separately, and requires the dedicated overwrite approval.
- [ ] Non-tty run with unanswered prompts emits `GENTLE_AI_WF_REFRESH_NEEDS` and a clear exit code; `WF_REFRESH_RESUME=1` re-enters R5 with staging intact; no orphaned `.wizard-staging/`/`refresh-plan.json`.
- [ ] `DEPRECATED_PATHS` covers per-IDE skills dirs + `wf-sdd-lite`; `AI_DEV_WORKFLOW.md:765` wording matches reality.
- [ ] `AI_DEV_WORKFLOW.md` R1/R4/R5/R6 sections (709, 762, 765-767, 1699-1710) updated in the same change.
- [ ] No commits without user review.