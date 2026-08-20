# Design: Fix `/wf-refresh` field report defects

**Change**: `fix-wf-refresh-field-report`  
**Status**: Design  
**Created**: 2026-08-20

## Technical Approach

Regeneration-first with merge for FU2/FU3, surgical coalescing helper for FU1, DEPRECATED_PATHS extension for FU4, non-tty manifest+resume for FU5, apply-only plain `rm` for FU6, `local_modified` flag for FU7, R2 normalization, and doc-sync in the same change. All changes are deterministic, bash/python-3-stdlib only, and implementable as work-unit-per-fix with clear boundaries.

## Architecture Decisions

### Decision: FU1 — Coalescing Mechanism

**Choice**: New `_coalesce(state, path, default)` helper in `builder-core.py` used by both quality-guard (line ~301) and deploy workflow (line ~490). Not hardening `get_state_value` — that would alter unrelated callers.

**Alternatives**: (b) harden `get_state_value` to treat `""`/`null` as absent.

**Rationale**: Surgical, zero behavioral risk elsewhere. The helper does `val = get_state_value(state, path, None); return default if val in (None, "") else val`. Called at the two replacement sites only.

### Decision: FU2/FU3a — Commands Always Re-detected + Bullets

**Choice**: R1 always re-detects script names from `package.json` (FU2) and emits a **bulleted** list merged with descriptions from the current AGENTS.md Commands section. The merged bullets are written back to `discovery.commands` (state) so the builder renders them verbatim — no builder change needed.

**Alternatives**: Builder-side bullet renderer (changes builder-core; couples rendering to builder).

**Rationale**: State already stores commands as opaque text; writing merged bullets there preserves the builder's verbatim contract. R1 already parses AGENTS.md sections with `_wf_section` — extend it to extract `name -> description`.

### Decision: FU3b — Code Style Compose from Structured Conventions

**Choice**: `infer_placeholder("discovery.conventions.code_style")` in `builder-core.py` (~472-477) composes bullets from `discovery.conventions.{naming,components,imports,tests,css,state}` when any is present (format: `- Naming: <value>`, `- Components: <value>`, etc.). Falls back to preserving the current AGENTS.md section when ALL structured fields are absent.

**Rationale**: The structured fields have existed in state since wf-init phase4 but the builder ignored them (only used `naming`). Composing is deterministic, no agent pass needed, and the template `AGENTS.router.md:30-32` renders the body verbatim — zero template change.

### Decision: FU3c — Structure from Live Tree + Comment Merge

**Choice**: R1 regenerates a tree snippet via deterministic `find` (capped depth 2, exclude `node_modules/.git/dist/.wizard-*`). Merges comments from the old AGENTS.md `## Project Structure` section by path-name match (exact dir name); new paths render without comment. Written to `discovery.conventions.structure`.

**Rationale**: Tree is derivable; comments are semantic (not derivable). Merge preserves intent where structure is stable.

### Decision: FU3d — MCPs Re-detect + 3-Column Table

**Choice**: R1 re-detects known MCP config files (`.mcp.json`, `.cursor/mcp.json`, `.windsurf/mcp.json`, `.github/copilot-instructions.md` hints). Merges `purpose`/`setup` from the old AGENTS.md MCP table (parse 3-col `| MCP | Purpose | Required setup |`). Extends `state.mcps` entries with optional `purpose`/`setup` (schema-compatible). `builder-core.py` `infer_placeholder("mcps.table")` (~497-512) renders 3-col when `purpose` present, else 2-col fallback.

**Rationale**: Canonical table shape is documented at `AI_DEV_WORKFLOW.md:1704` (3 cols). Config files give names; purposes are semantic (only in old AGENTS.md or state). Extending entries avoids schema break.

### Decision: FU3e — Fallback Rule ("Richer Wins")

**Choice**: Concrete per-field procedure:
- **Commands/Structure/MCPs**: Regenerated content supersedes stale preserved text; preserved (old AGENTS.md) wins only over FLAT state values for fields that CANNOT be regenerated (none for these three — all derivable).
- **Code Style**: Composed from structured conventions (when present) > preserved old section > fallback "camelCase".
- R5 diff preview is the final safety net for all.

### Decision: FU4 — DEPRECATED_PATHS Per-IDE Skills

**Choice**: Extend R4 `DEPRECATED_PATHS` array with per-IDE skill dirs for 6 deprecated commands (`wf-cicd`, `wf-cleanup`, `wf-refresh`, `wf-init`, `wf-sdd-config`, `wf-sdd-lite`) under 8 IDE skill roots: `.claude/skills/`, `.cursor/skills/`, `.opencode/skills/`, `.windsurf/skills/`, `.codex/skills/`, `.kiro/skills/`, `.github/skills/`, `.devin/skills/` (`.devin` only when windsurf active, per `reinsert_legacy_bridge`). Guard: `present on disk AND absent from staging` + dedup + R5 approval — same as existing command paths.

### Decision: FU5 — Non-tty Manifest + Resume

**Choice**: `_ask_yesno_safe` (refresh-lib.sh ~217-272) records pending prompt in a global array instead of `exit 2`; returns sentinel. R5 (before any approval gate) collects ALL pending prompts from R-1/R1/R2/R5 phases and emits `GENTLE_AI_WF_REFRESH_NEEDS="prompt=<p1>|prompt=<p2>|...|apply_mode=..."` with exit code 3 (distinct from abort 2). `WF_REFRESH_RESUME=1` skips R-1..R4 (validates staging/plan exist) and re-enters R5 with staging intact. Abort paths in R-1/R1/R2/R4 either clean staging/plan or print exact resume instructions. Phases firing prompts: R-1 (update global), R1 (use updated info), R2 (feature enables), R5 (approvals + apply gate).

### Decision: FU6 — Apply-only Plain `rm`

**Choice**: R6 (~1498,1509) uses `rm -f` when `APPLY_ONLY == true`, `git rm -f` only in commit mode. Closing message (~1686) corrected: "changes left in the working tree (unstaged)" now accurate for all categories.

### Decision: FU7 — Local-modified Flag + Dedicated Approval

**Choice**: R4 marks `updated` entries with `local_modified: true` when `git diff --quiet HEAD -- <file>` fails (working tree ≠ HEAD). Fallback: compare against recorded `old_hash` when no HEAD. R5 dedicated warning block + dedicated approval `Overwrite locally-modified files?` stored as `build_plan.approval.overwrite_local`. R6 copies those files only when that approval is true. `refresh-plan.json` gains `local_modified` on `updated` entries — R5/R6 consumers in same work unit.

### Decision: R2 Normalization

**Choice**: R2 (`migrate_state` / R2 block) adds idempotent jq: `if .discovery.node_engine in ["", "None"] then .discovery.node_engine = null else . end | if .discovery.npm_major in ["", "None"] then .discovery.npm_major = null else . end`. Runs on every refresh, harmless on clean state.

### Decision: Doc-sync

**Choice**: Update `AI_DEV_WORKFLOW.md` inline with the same change: R1 (~709), R4 (~762, 765-767), R5/R6 (~767), MCP table canonical shape (~1699-1710) to match the 3-column renderer. Part of this change per AGENTS.md sync rule.

## Data Flow

```
R1 (always re-detect commands + regen structure + regen MCPs)
    → merged commands bullets (descriptions from old AGENTS.md)
    → composed code_style (from conventions.*)
    → tree + merged comments
    → MCPs 3-col (purpose/setup from old AGENTS.md)
    → writes to state (discovery.commands, conventions.code_style, conventions.structure, mcps[])
    ↓
Builder renders verbatim from state (commands bullets, code_style bullets, structure, mcps table)
    ↓
R4 classifies files (with local_modified flag for updated entries)
    ↓
R5 shows diff, collects approvals (including overwrite_local)
    ↓
R6 applies (plain rm for apply-only, correct message, respects overwrite_local)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `wf-init/lib/builder-core.py` | Modify | Add `_coalesce` helper; update quality-guard (`:301`) and deploy (`:490`) to use it; compose code_style bullets in `infer_placeholder`; render mcps 3-col when purpose present |
| `wf-init/lib/refresher.md` | Modify | R1: always re-detect commands; parse AGENTS.md Commands/Structure/MCPs for merge; regen structure from live tree; regen MCPs from configs + merge; write merged to state. R4: extend DEPRECATED_PATHS with per-IDE skills; add local_modified detection. R5: non-tty manifest+resume; dedicated overwrite_local approval. R6: plain rm in apply-only; respect overwrite_local; correct message. |
| `wf-init/lib/state-helpers.sh` | Modify | `_ask_yesno_safe`: record pending prompts instead of exit 2; return sentinel. |
| `AI_DEV_WORKFLOW.md` | Modify | Update R1/R4/R5/R6 phase docs + MCP table canonical shape to match 3-col renderer. |
| `openspec/changes/refactor-wf-refresh-builder-driven/design.md` | N/A | (Reference only — this change creates its own design.md) |

## Interfaces / Contracts

- **`refresh-plan.json` schema addition**: `updated[]` entries gain `local_modified: boolean` (default false). Backwards-compatible (missing = false).
- **`state.mcps` entries**: optional `purpose: string`, `setup: string` added. Backwards-compatible.
- **Non-tty protocol**: `GENTLE_AI_WF_REFRESH_NEEDS="prompt=...|...|apply_mode=..."` emitted on exit 3; `WF_REFRESH_RESUME=1` re-enters R5 with staging intact.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `_coalesce`, code_style compose, mcps 3-col renderer | `python3 -m py_compile` + inline asserts in builder-core.py |
| Integration | R1 commands re-detect + merge, R4 local_modified, R5 manifest, R6 apply-only | Fixture dry-runs (a–e from proposal): `bash -n` on refresher blocks + scripted scenarios with temp git repos |
| E2E | Full `/wf-refresh` on test projects: node-empty, commands-drift, rich-AGENTS.md, apply-only, local-modified, non-tty | `bash` simulation scripts (no test runner; manual review + git diff) |

## Threat Matrix

N/A — no routing, shell subprocess changes beyond existing bash patterns, VCS/PR automation unchanged (R6 still uses explicit pathspec), executable-file classification unchanged, process integration unchanged.

## Migration / Rollout

R2 normalization handles already-corrupted state (`"None"`/`""` → `null`). No feature flags; fixes ship in next release. `/wf-refresh` pulls `refresher.md` from remote `main` — consumers pick up fixes only after push.

## Open Questions

- None — all mechanism choices resolved per the decisions above.

---

**Design artifact target**: `openspec/changes/fix-wf-refresh-field-report/design.md` (OpenSpec) + Engram `sdd/fix-wf-refresh-field-report/design` (hybrid mode).