# Proposal: Refactor `/wf-refresh` to builder-driven migration mechanism

**Change**: `refactor-wf-refresh-builder-driven`  
**Status**: Proposal  
**Created**: 2026-08-13

## Problem statement

The current `/wf-refresh` implementation is fragile and incomplete:

1. **Duplicate rendering logic**: `/wf-refresh` has its own bash template engine that diverges from the Builder used in `/wf-init`. Every new IDE, command, skill, or variant must be updated in two places.
2. **Incomplete file tracking**: `WIZARD_MANIFEST.json` is static and does not track the full set of generated files or their expected deletion.
3. **No deletion mechanism**: Deprecated files (e.g., old `wf-cicd`, retired skills) are never removed.
4. **Risk of deleting user skills**: Current cleanup logic uses broad `*` patterns that can mark user skills (e.g., `react-19`, team skills) as wizard artifacts.
5. **Custom AGENTS.md rules not preserved**: Custom rules without explicit `<!-- WF: DO NOT REGENERATE -->` markers can be lost during regeneration.
6. **State/schema drift**: New features or tool versions are not migrated into `.wizard-state.json` automatically.
7. **Per-IDE skills out of sync**: Phase 3.5 only checks commands and the universal `.agents/skills/` fallback; native per-IDE skills are not verified.

## Objective

Make `/wf-refresh` a **safe, deterministic migration runner** that:
- Reuses the Builder (`B1-B9`) from `/wf-init` as the single source of truth
- Compares generated staging files with the project using SHA256 hashes
- Detects and proposes additions, updates, and deletions of wizard-managed files
- Preserves user skills and custom AGENTS.md rules
- Supports forward migration from any version with a valid `.wizard-state.json`
- Never deletes user files without explicit approval

## Scope

### Included

- Create `wf-init/lib/refresher.md` with phases R-1 through R6 (global command refresh, project discovery, state migration, builder re-run, hash-based diff, review gate, apply and close)
- Create `wf-init/lib/migrations.md` for state/schema migrations
- Extend `wf-init/lib/state.md` schema: add `build_plan.generated_files[]` and `build_plan.managed_paths[]`
- Update Builder files to register generated files and preserve custom AGENTS.md content
- Rewrite `templates/commands/wf-refresh/_base.md` to orchestrate the refresher
- Deprecate `WIZARD_MANIFEST.json` from the refresh flow and remove its generator from `release-please.yml`
- Update docs (`WF_REFRESH_TROUBLESHOOTING.md`, `AI_DEV_WORKFLOW.md`)

### Excluded

- Pre-flight optimization (Opción C: skip builder if nothing changed) — deferred to iteration 2
- Changes to `/wf-cleanup` or `/wf-settings` beyond compatibility fixes
- Refactoring existing Builder logic (only extend it)

## Approach

### Option A: Full builder + hash diff (chosen)

1. **Global command refresh** (Phase R-1): Update `wf-init`, `wf-refresh`, `wf-cleanup` if outdated
2. **Project discovery** (Phase R1): Re-run discovery to detect drift
3. **State migration** (Phase R2): Migrate schema and ask about new features
4. **Builder re-run** (Phase R3): Generate everything into `.wizard-staging/`
5. **Hash-based diff** (Phase R4): Compare SHA256 of each file; classify as `add`, `update`, `delete`, or `unchanged`
6. **Review gate** (Phase R5): Show grouped diff; require explicit approval for deletions
7. **Apply and close** (Phase R6): Copy approved changes, update state, commit, clean staging

### Why this approach

- **Single source of truth**: Reuses Builder; scales to new releases automatically
- **Deterministic**: Hash-based comparison is reproducible and correct
- **Safe**: Explicit approval gates; never auto-delete user files
- **Efficient**: Unchanged files are skipped (not re-copied)
- **Preserves custom content**: Explicit markers for user-maintained sections

## Key design decisions

| Decision | Rationale |
|----------|-----------|
| Reuse Builder (B1-B9) | Single source of truth; no parallel rendering engines |
| Hash-based comparison | Avoids re-writing identical files; detects real changes |
| `.wizard-managed-files.json` | Tracks what wizard owns; enables safe deletion detection |
| Explicit deletion approval | Never auto-delete; user controls what goes away |
| Preserve `<!-- WF: DO NOT REGENERATE -->` | Respects custom AGENTS.md rules and user skills |
| Deprecate `WIZARD_MANIFEST.json` | Dead code once refresh is builder-driven |
| Opción A for MVP | Full builder + hash diff is simple and correct; Opción C (pre-flight) deferred |

## Files to create/modify

### New files (3)
- `wf-init/lib/refresher.md` — orchestrator for phases R-1 to R6
- `wf-init/lib/migrations.md` — state/schema migration rules
- `openspec/changes/refactor-wf-refresh-builder-driven/` — SDD artifacts (this proposal)

### Modified files (10)
- `wf-init/lib/state.md` — extend `build_plan` schema
- `wf-init/lib/builder.md` — register generated files, preserve custom AGENTS.md
- `wf-init/subagent-builder-core.md` — record files in `build_plan`
- `wf-init/subagent-builder-heavy.md` — record files in `build_plan`
- `wf-init/phase8.md` — write `.wizard-managed-files.json`
- `templates/commands/wf-refresh/_base.md` — rewrite to use refresher
- `templates/commands/wf-cleanup/_base.md` — remove manifest dependency
- `.github/workflows/release-please.yml` — remove `update-manifest` job
- `WF_REFRESH_TROUBLESHOOTING.md` — update docs
- `AI_DEV_WORKFLOW.md` — update docs

## Risks and mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Builder bug affects both `/wf-init` and `/wf-refresh` | Medium | Single source of truth is correct tradeoff; add focused tests; review gate before commit |
| Deleting user edits or custom skills | High | Only delete files in old `managed_paths` with matching SHA256; warn if hash differs; never delete files outside known wizard patterns |
| Losing custom AGENTS.md rules | Medium | Use explicit markers; show full diff if no markers; require approval |
| Schema migrations fail on old projects | Medium | Support migrations from any version with valid `.wizard-state.json`; test with archived manifests |
| Removing manifest breaks release-please | Low | Remove only `update-manifest` job, not release creation; keep files as historical artifacts |
| CI/CD runtime setup runs unnecessarily | Low | Only run if missing (idempotent detection); e.g., `npx husky init` only if `.husky/` does not exist |

## Assumptions

1. **Opción A is chosen**: Full builder + hash diff for MVP (Opción C deferred)
2. **Wizard-managed patterns**: Files matching `wf-*/SKILL.md`, `.github/workflows/*`, `.husky/*`, etc.
3. **Custom content markers**: Already documented in `wf-refresh/_base.md` and `phase2.md`
4. **`.wizard-staging/` is available**: Confirmed it is deleted at end of `/wf-init` (phase8.md line 500)
5. **State schema can be extended**: `build_plan` can add `generated_files[]` and `managed_paths[]` without breaking `/wf-init`

## Open questions

1. **Pre-flight optimization**: Should we implement Opción C (skip builder if nothing changed) in this iteration or defer to iteration 2?
   - **Decision**: Defer to iteration 2; Opción A is simpler and correct for MVP
2. **Manifest deprecation timeline**: Should we delete `WIZARD_MANIFEST.json` and `.wizard-manifests/` immediately or keep as historical artifacts?
   - **Decision**: Keep as historical artifacts; remove in follow-up PR after proving no external dependency
3. **CI/CD runtime setup**: Should `npm install` / `husky init` / `gga install` be auto-run or require explicit confirmation?
   - **Decision**: Only run if missing (idempotent); pause and ask for `gga install` (modifies git hooks)

## Success criteria

- [ ] `/wf-refresh` successfully re-runs Builder and generates correct staging
- [ ] Hash-based diff correctly identifies `add`, `update`, `delete`, `unchanged` files
- [ ] User skills are never deleted (protected by pattern + hash matching)
- [ ] Custom AGENTS.md rules inside markers are preserved
- [ ] State migrations work for projects from `0.6.4-beta` to `0.6.8-beta`
- [ ] Simulation tests pass: no-change, enable-feature, custom-content, deprecation scenarios
- [ ] All docs updated and consistent with implementation
- [ ] No commits until user approval

## Next steps

1. **Specification phase**: Detailed spec for each phase (R-1 to R6)
2. **Design phase**: File structure, data flow, error handling
3. **Tasks phase**: Break into reviewable work units
4. **Implementation**: Create files, update Builder, rewrite `/wf-refresh`
5. **Verification**: Run simulation tests, review diffs, commit

---

**Approval gate**: ¿Apruebas este plan de implementación?
