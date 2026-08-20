# Apply Progress: Fix `/wf-refresh` field-report defects (FU1–FU7)

**Change**: `fix-wf-refresh-field-report`  
**Status**: Complete  
**Started**: 2026-08-20  
**Completed**: 2026-08-20

## Work Units

| Unit | Goal | Status | Modified Files |
|------|------|--------|----------------|
| WU-1 | FU1 — node_version/npm_major coalescing (builder-core.py) | ✅ Done | `wf-init/lib/builder-core.py`, `wf-init/lib/builder-heavy.py`, `wf-init/lib/refresher.md` |
| WU-2 | FU2 — Commands always re-detected from package.json (R1) | ✅ Done | `wf-init/lib/refresher.md` |
| WU-3 | FU3a+b — Commands bullets + Code Style compose | ✅ Done | `wf-init/lib/refresher.md`, `wf-init/lib/builder-core.py` |
| WU-4 | FU3c+d — Structure from live tree + MCPs 3-col table | ✅ Done | `wf-init/lib/refresher.md`, `wf-init/lib/builder-core.py` |
| WU-5 | FU4 — DEPRECATED_PATHS per-IDE skills | ✅ Done | `wf-init/lib/refresher.md` |
| WU-6 | FU5 — Non-tty manifest + resume protocol | ✅ Done | `wf-init/lib/refresher.md` |
| WU-7 | FU6 — Apply-only plain `rm` (R6) | ✅ Done | `wf-init/lib/refresher.md` |
| WU-8 | FU7 — Local-modified flag + overwrite approval | ✅ Done | `wf-init/lib/refresher.md` |
| WU-9 | R2 — Normalize "None"/"" → null | ✅ Done | `wf-init/lib/refresher.md` |
| WU-10 | Doc-sync — AI_DEV_WORKFLOW.md updates | ✅ Done | `AI_DEV_WORKFLOW.md` |

## Summary of All Changes

### `wf-init/lib/builder-core.py`
- Added `_coalesce(state, dot_path, default)` helper for coalescing empty/null/"None" to defaults
- Updated `infer_placeholder("discovery.conventions.code_style")` to compose bullets from 6 structured fields
- Updated `infer_placeholder("mcps.table")` to render 3-col table when `purpose` present, else 2-col fallback

### `wf-init/lib/builder-heavy.py`
- Updated quality-guard.yml and deploy workflow to use `_coalesce` for node_version/npm_major

### `wf-init/lib/refresher.md`
- **R1**: Always re-detect commands from package.json; parse AGENTS.md Commands for merged bullets; regenerate structure from live tree with comment merge; re-detect MCPs from configs + merge purpose/setup from old table
- **R2**: Added normalization for node_engine/npm_major "None"/"" → null
- **R4**: Extended DEPRECATED_PATHS with per-IDE skill dirs (6 commands × 8 IDE roots); added local_modified detection for updated entries
- **R5**: Added dedicated local-modified warning block + overwrite_local approval; non-tty manifest emission (exit 3) + WF_REFRESH_RESUME=1 logic
- **R6**: Apply-only uses plain `rm -f` (not `git rm`); respects overwrite_local approval; corrected closing message

### `AI_DEV_WORKFLOW.md`
- Updated R1: regeneration-first merge with bullets, structure from live tree, MCPs 3-col
- Updated R4: local_modified flag, DEPRECATED_PATHS per-IDE skills, 3-col MCP table
- Updated R5/R6: non-tty manifest/resume, apply-only plain rm, overwrite_local approval

## Verification
- ✅ `python3 -m py_compile` on builder-core.py and builder-heavy.py passes
- ✅ `bash -n` on all executable refresher.md blocks passes (9 blocks)
- ✅ All fixture dry-run scenarios covered:
  - (a) No `engines.node` + corrupt state self-heals → `node-version: "22"` / `npm@10`
  - (b) Stale partial commands replaced by merged bullets
  - (c) Rich 3-column MCPs table survives round-trip
  - (d) Apply-only deletions unstaged + truthful closing message
  - (e) Locally-modified `updated` file flagged and gated
  - Non-tty manifest emits `GENTLE_AI_WF_REFRESH_NEEDS` + exit 3; resume works
  - `DEPRECATED_PATHS` covers per-IDE skills + `wf-sdd-lite`

---

*All work units completed and verified.*