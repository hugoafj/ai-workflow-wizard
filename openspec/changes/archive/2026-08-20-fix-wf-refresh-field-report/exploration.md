# Exploration: Fix `/wf-refresh` field report defects (FU1–FU7)

**Change name**: `fix-wf-refresh-field-report`

**Scope**: Bug-fix consolidation for the builder-driven `/wf-refresh` pipeline (`wf-init/lib/refresher.md` + `wf-init/lib/builder-*.py` + `wf-init/lib/refresh-lib.sh` + documentation).

**Method note — plan-mode vs fresh verification**: The seven defects (FU1–FU7) below were first identified in plan mode. This exploration re-verified **every claim against the current working tree** (commit `5e8b0e2`, the head of the `fix(wf-refresh)` series). Results: FU1, FU2, FU3a, FU3b, FU5, FU6, FU7 are **confirmed as stated**; **FU4 is substantially stale/wrong as stated** — the current `DEPRECATED_PATHS` *does* include per-IDE command paths and the wf-sdd-config entries; the real remaining gap is per-IDE **skills** paths plus the archived `wf-sdd-lite` command. FU4 is documented below in its corrected form with full evidence.

---

## Current state analysis

`/wf-refresh` is orchestrated by `wf-init/lib/refresher.md` (1722 lines), which:

1. Writes a helper library `wf-init/lib/refresh-lib.sh` (heredoc, line 33) containing `_ask_yesno_safe`, `_ask_yesno`, `_apply_jq_filter`, `migrate_state`, etc.
2. Runs phases R-1 (global version check), R0 (pre-flight), R1 (project content drift + AGENTS.md backfill), R2 (state migration), R3 (builder re-run via `builder-core.py`/`builder-heavy.py`), R4 (hash-based diff → `refresh-plan.json`), R5 (review gate), R6 (apply + commit + promote staging state).
3. Is the single consumer of `.wizard-staging/`, `.wizard-refresh-baseline.json`, and `refresh-plan.json`.

No automated test runner exists (markdown/templates repo, strict TDD false). Verification is manual review plus `bash -n`/`python3 -m py_compile` syntax checks and scenario dry-runs.

## Verified findings (FU1–FU7)

### FU1 — `node-version`/`npm_major` render empty or `"None"` in `quality-guard.yml`

**Status: CONFIRMED (and worse than stated — two manifestations)**

- `wf-init/lib/builder-heavy.py:301-302`:
  ```python
  qg = qg.replace("{{node_version}}", str(builder_core.get_state_value(state, "discovery.node_engine", "22")))
  qg = qg.replace("{{npm_major}}", str(builder_core.get_state_value(state, "discovery.npm_major", "10")))
  ```
- `builder-core.py:54-61` `get_state_value()` returns `default` **only when the key is absent**; a present-but-empty/`null` value is returned as-is. `str(None)` → `"None"`.
- **Two broken states exist in practice**:
  - `state.md:67-68` declares the schema defaults `"node_engine": null, "npm_major": null` → untouched/newly-migrated state renders `node-version: "None"` and `npm install -g npm@None`.
  - `refresher.md` R1 writes `NODE_ENGINE=""` (empty string) when `package.json` has no `engines?.node` (`node -e "...engines?.node||''"`) and, on accepted drift, stores `.discovery.node_engine = ""` → renders `node-version: ""`.
- The template contract `templates/protocols/cicd/variants/quality-guard.yml.md:4-5` says `{{node_version}} → project engines.node, or 22 by default`; the "or 22 by default" branch is unreachable once the key exists with an empty/`null` value.

### FU2 — R1 never re-detects `commands` when state already holds a value

**Status: CONFIRMED**

- `refresher.md` R1 (≈lines 723-730):
  ```bash
  COMMANDS="$OLD_COMMANDS"
  if [[ -z "$COMMANDS" && -f package.json ]] && command -v jq >/dev/null 2>&1; then
    COMMANDS=$(jq -r '[.scripts | keys[] | "npm run " + .] | join(", ")' package.json ...)
  fi
  ```
- Re-detection is gated on the state value being empty, so when `.wizard-state.json` holds an old/partial list (e.g. 4 scripts while `package.json` now has 12), `OLD_COMMANDS == COMMANDS` and the drift gate `[[ "$OLD_COMMANDS" != "$COMMANDS" ]]` never fires. The stale list is written back to staging and rendered into AGENTS.md.

### FU3 — regenerated AGENTS.md flattens rich content (two independent causes)

**Status: CONFIRMED (both causes)**

- **FU3a — backfill only runs when the staging field is empty**: `refresher.md` R1 guards each backfill with `if [[ -z "$(jq -r '.discovery.commands // ""' "$STAGING_STATE_BF" ...)" ]]` (same pattern for `conventions.code_style`, `conventions.structure`, `mcps`). A partial value in state (e.g. the FU2 stale commands list) blocks preservation of the rich current AGENTS.md section (bullets with descriptions).
- **FU3b — MCP table is reduced to `{name, active}` end-to-end**:
  - Backfill parse (`refresher.md` R1): `awk -F'|'` reads only `name=$2; active=$3` → for the documented 3-column table (`AI_DEV_WORKFLOW.md:1699-1710`: `| MCP | Purpose | Required setup |`), `active` receives the Purpose text and is coerced to `true` unless it is exactly `no`.
  - Render (`builder-core.py` `infer_placeholder("mcps.table")`, ≈497-512): emits only `| MCP | Active |` rows; `Purpose`/`Required setup` columns are dropped.
  - Net effect: a refresh re-writes the `## Project MCPs` section losing the Purpose/Required-setup documentation the current AGENTS.md carries.

### FU4 — deprecated-path cleanup gaps (CORRECTED from plan-mode claim)

**Status: PARTIALLY STALE AS STATED — verified against current tree**

Plan mode claimed: *"DEPRECATED_PATHS only lists `.agents/skills/wf-sdd-config/SKILL.md` and `.agents/protocols/wf-sdd-config.md`; the other deprecated commands have per-IDE paths"* — **this is not what the code says today**.

- `refresher.md:1148-1152` (current) **does** include per-IDE **command** paths for `wf-cicd`, `wf-cleanup`, `wf-refresh`, `wf-init` (`.windsurf/workflows/`, `.claude/commands/`, `.cursor/commands/`, `.opencode/commands/`, `.codex/commands/`, `.kiro/steering/`, `.github/prompts/`), plus `.agents/protocols/wf-cicd.md`, `.agents/skills/wf-{cicd,cleanup,refresh,init}/SKILL.md`, **and** `.agents/skills/wf-sdd-config/SKILL.md` + `.agents/protocols/wf-sdd-config.md`. So "wf-sdd-config is not deleted" is also false — it is listed (and templates/ has **zero** matches for `wf-sdd-config`, confirmed: `grep -c` = 0 across all template files, so the entries are correct safety-net removals).
- **The real remaining gaps**:
  1. **Per-IDE *skills* paths for the four deprecated commands are missing**: install.sh (lines 134-193) and `meta.md:40-42` document native per-IDE skills dirs — `.claude/skills/`, `.cursor/skills/`, `.codex/skills/`, `.config/opencode/skills/`, `.windsurf/skills/`, `.kiro/skills/`, `.devin/skills/`, `.github/skills/` — but `DEPRECATED_PATHS` only covers `.agents/skills/`. Legacy projects initialized by pre-0.8 wizard versions can carry e.g. `.claude/skills/wf-init/SKILL.md` and it will never be cleaned.
  2. **Archived command `wf-sdd-lite` is omitted**: `templates/_archive/wf-sdd-lite/` exists and `wf-cicd` (also archived, `templates/_archive/wf-cicd/`) *is* listed — inconsistent; `wf-sdd-lite` appears nowhere in `refresher.md`/`install.sh`/`meta.md`.
  3. **Doc↔code drift**: `AI_DEV_WORKFLOW.md:765` claims DEPRECATED_PATHS covers "per IDE plus their skills/protocols" — overstated (per-IDE skills are NOT covered). `meta.md:17-19` is the canonical per-IDE table the list should be derived from (or shared with).

### FU5 — non-tty abort orphans staging artifacts; no resume path

**Status: CONFIRMED**

- `_ask_yesno_safe` (refresh-lib.sh, `refresher.md` ≈217-282): in non-tty, with no `WF_REFRESH_ANSWERS` entry and no `WF_REFRESH_DEFAULT_ANSWER` (and no `cancel` second arg), it prints a developer-oriented error and `exit 2` — it does **not** return "no".
- Cleanup exists only in two places: the R6 EXIT trap (`cleanup_r6`, `refresher.md` ≈1439-1445) and the R5 "cancel" choice (≈1398-1402). R-1, R1, R2, R4 and the R5 category prompts install **no** trap, so an `exit 2` there (e.g. the R1 `_ask_yesno_safe "Use updated project info?"`, R2 feature prompts, R5 "Apply added files?" prompts, or the R5 apply-gate `exit 2` when `WF_REFRESH_APPLY_MODE` is unset) leaves `.wizard-staging/`, `refresh-plan.json`, and `.wizard-refresh-baseline.json` orphaned.
- No resume path: re-running `/wf-refresh` restarts at R-1; nothing records phase progress.

### FU6 — apply-only mode leaves a mixed git state (deletions staged, edits unstaged)

**Status: CONFIRMED**

- `refresher.md` R6: deletions use `git rm -f --ignore-unmatch --pathspec-from-file=...` for both `deleted` (≈1501-1510) and `deleted_modified` (≈1517-1526), executed **before** the `APPLY_ONLY` branch and **unconditionally** in apply-only mode.
- Added/updated files are `cp`'d to the working tree (unstaged), and the apply-only branch only wraps `git add`/`git commit` (≈1630+).
- Result: in apply-only mode the user gets staged **deletions** mixed with unstaged **modifications**, while the message says "Apply-only mode: changes left in the working tree (unstaged)." — false for deletions. Also `.gitignore` is mutated (via `_gi_add`, outside the apply-only branch) with no commit, which is fine for review but must be part of the eventual manual commit.

### FU7 — `updated` files with local uncommitted changes are silently overwritten

**Status: CONFIRMED**

- R4 classifies `updated` purely by `STAGING_HASH != PROJECT_HASH` (≈1078-1087) — it never compares the project file against `HEAD` or the recorded `generated_files` hash.
- `deleted_modified` (the "user edited this" category, ≈1109-1141) exists **only for files being deleted**; an `updated` file with local uncommitted changes is neither flagged nor warned about, and R6 `cp`s the staged version over it silently (≈1493-1499).
- Mitigating factor: the R5 preview for updated files is `diff -u "$file" "$STAGING/$file"`, which does show the user's local edits — so a careful reviewer can notice — but there is no explicit classification, warning, or preservation path.

## Affected areas

| File | Role | Defects |
|---|---|---|
| `wf-init/lib/refresher.md` | Refresh orchestrator (R-1..R6) + embedded `refresh-lib.sh` | FU2, FU3a, FU3b, FU4, FU5, FU6, FU7 |
| `wf-init/lib/builder-heavy.py` | Renders quality-guard.yml placeholders | FU1 |
| `wf-init/lib/builder-core.py` | `get_state_value` (line 54), `mcps.table` render (≈497-512) | FU1, FU3b |
| `wf-init/lib/state.md` | Schema defaults `node_engine: null`, `npm_major: null` (lines 67-68) | FU1 |
| `templates/protocols/cicd/variants/quality-guard.yml.md` | Template contract (lines 4-5, 36, 40) | FU1 (doc side) |
| `templates/commands/meta.md` | Canonical per-IDE installation table (lines 17-19, 40-42) | FU4 (source of truth for the list) |
| `install.sh` | Global per-IDE install/uninstall paths (lines 134-193, 226-257) | FU4 (evidence of per-IDE skills dirs) |
| `AI_DEV_WORKFLOW.md` | R-phase documentation (lines 760-767, 1699-1710) | FU1 doc, FU3b doc, FU4 doc drift |
| `templates/_archive/wf-sdd-lite/` | Archived command not covered by cleanup | FU4 |

## Approaches

Because the seven defects share the same orchestrator and the same doc/code contract, the recommended shape is **one fix change with tasks grouped per defect** (not seven micro-changes).

1. **FU1 — coerce empty/null to defaults at the builder boundary** (recommended)
   - Add a `_coalesce(value, default)` helper in `builder-core.py` (or harden `get_state_value`) so `""`, `None`, and missing all fall through to `"22"`/`"10"`; additionally guard R1's drift write to **skip writing empty** `node_engine`/`npm_major` (don't overwrite a good stored value with `""`).
   - Pros: single point of truth; fixes both `"None"` and `""` manifestations; low effort.
   - Cons: doesn't fix already-corrupted state values (`"None"` string) — consider a state-migration normalization in R2.
   - Effort: Low.

2. **FU2 + FU3a — always re-detect; backfill rich sections on stale/fallback values** (recommended)
   - Change R1 to detect commands/fields **unconditionally** and only fall back to the stored value when fresh detection yields nothing; change the backfill guard from "only when empty" to "when the state value equals the builder's generic fallback (`npm run build`/`camelCase`/`flat`/`None configured`) or is stale (differs from the fresh detection)".
   - Pros: removes both stale-commands and flattening defects with one mechanism; preserves the "never overwrite a rich state" intent.
   - Cons: needs careful diffing semantics to avoid clobbering user-curated sections that legitimately differ from fresh detection (mitigate: only backfill when current AGENTS.md section is richer than the flat value — e.g. multi-line).
   - Effort: Medium.

3. **FU3b — carry MCP table columns through the whole chain** (recommended)
   - Extend the R1 backfill parser to preserve extra columns (store `{name, active, purpose, required_setup}` or keep the raw table body as `mcps.raw_table`); extend `builder-core.py` `mcps.table` to render a 3-column `| MCP | Purpose | Required setup |` matching `AI_DEV_WORKFLOW.md:1699-1710`; update the doc if the canonical shape changes.
   - Pros: stops documented information loss; aligns renderer with the documented format.
   - Cons: needs a schema note in `state.md`; legacy state with 2-column `mcps` arrays still renders 3-column table with empty Purpose (acceptable).
   - Effort: Medium.

4. **FU4 — derive DEPRECATED_PATHS from the canonical per-IDE table** (recommended, corrected scope)
   - Extend the list with per-IDE skills dirs (`.claude/skills/`, `.cursor/skills/`, `.codex/skills/`, `.config/opencode/skills/`, `.windsurf/skills/`, `.kiro/skills/`, `.devin/skills/`, `.github/skills/`) for the four commands, plus `wf-sdd-lite` (commands + skills + protocols); best long-term: generate the list from `meta.md`/`install.sh` instead of a hardcoded array; fix `AI_DEV_WORKFLOW.md:765` wording.
   - Pros: closes the actual gap; removes the doc drift.
   - Cons: hardcoded list growth is repetitive (mitigate with loops over IDEs × commands).
   - Effort: Low-Medium.

5. **FU5 — global cleanup trap + resume path** (recommended)
   - Install a cleanup trap once at R-1/R0 (idempotent, guarded by a `WF_REFRESH_KEEP_STAGING`/`--keep` escape hatch for debugging) instead of relying on R6's trap and R5's cancel; optionally record `refresh_progress` in the staging state for resume.
   - Pros: any abort (exit 2, network, Ctrl-C) leaves the tree clean; cheap.
   - Cons: a keep-flag is needed so diagnostics aren't destroyed; resume is nice-to-have, not required for this change.
   - Effort: Low (trap) / Medium (resume).

6. **FU6 — apply-only must not stage deletions** (recommended)
   - In apply-only mode, delete with plain `rm -f` (or `git rm` without staging is impossible — use `rm` + leave deletion to the user's review), and fix the closing message; keep `git rm` only for commit mode.
   - Pros: apply-only truly means "working tree only, nothing staged"; one-line message fix.
   - Cons: user must `git add -A`/`git rm` themselves later — which is exactly what apply-only promises.
   - Effort: Low.

7. **FU7 — detect and surface `updated_modified`** (recommended)
   - In R4, for files classified `updated`, compare the project hash against `HEAD` (or the recorded `generated_files` hash when available) and move locally-modified files into a new `updated_modified` category that requires explicit approval (reusing the `deleted_modified` UX), with a warning and the diff shown at R5.
   - Pros: no silent data loss; symmetric with the existing `deleted_modified` handling.
   - Cons: adds a category to the plan schema and R5/R6 loops (moderate surface); `HEAD` may be missing in non-git projects (fall back to recorded hash, then treat as plain updated).
   - Effort: Medium.

## Recommendation

Adopt **one consolidated fix change** covering all seven defects (option set 1-7 above), because they all live in the same orchestrator + builder scripts and share the doc/code contract. Order of implementation by risk: FU1 and FU6 are low-risk, high-value and independent (do first); FU5 (trap) makes the whole pipeline safer for CI/agent runs; FU2/FU3a/FU3b fix the field-report flattening that motivates this change; FU4 and FU7 are coverage/safety completions. Manual verification plan (no test runner): `bash -n` on the refresher blocks, `python3 -m py_compile` on builder scripts, plus a scenario dry-run on a fixture repo with (a) no `engines.node`, (b) stale partial commands, (c) rich 3-column MCPs table, (d) apply-only run with deletions, and (e) an `updated` file with local edits.

## Risks

- FU2/FU3a merge semantics could overwrite user-curated sections if "stale" is defined too aggressively — keep the "only when richer/fallback" guard and preview at R5 (the existing `diff -u` preview is the safety net).
- FU4 list expansion must not delete **project-specific** commands the user installed intentionally (e.g. a customized `.claude/skills/wf-init/` the user wants to keep). The existing "delete only when not in staging" condition partially protects this; keep explicit R5 approval for deletions.
- FU7's new category changes the plan schema (`refresh-plan.json`) — R5/R6 consumers and the R6 commit path lists must be updated in the same change to avoid a mid-run abort.
- State already corrupted with literal `"None"`/`""` values won't self-heal from the FU1 builder fix alone — add a normalization step in R2 (or backfill "22"/"10" during R1 drift) and note it in the proposal.
- All fixes change `refresher.md` behavior — per AGENTS.md, `AI_DEV_WORKFLOW.md` (phases R1/R4/R5/R6 sections, lines 760-767) must be updated in the same change; do not commit code without the doc audit.

## Ready for proposal

**Yes.** All seven defects are confirmed against the current tree (FU4 in corrected form), with file:line evidence, fix approaches, and a verification plan. The proposal phase should consolidate them into one change with per-defect tasks and the doc-sync requirement, and decide whether FU5's resume path is in scope or deferred.