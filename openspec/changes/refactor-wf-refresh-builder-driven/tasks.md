# Tasks: Refactor `/wf-refresh` to builder-driven migration

**Change**: `refactor-wf-refresh-builder-driven`  
**Status**: Tasks  
**Created**: 2026-08-13

> **ARCHIVED — historical artifact.** This change has been archived and the
> implementation shipped in 0.7.0-beta.1. The plan below is kept for record only;
> two planned files were never created as separate files: schema migrations live
> inside `wf-init/lib/refresher.md` (migration functions), and there is no
> `wf-init/lib/migrations.md`. Do not re-create either file from this plan.

## Work units (reviewable, independent)

### WU-1: Extend state schema and migrations

**Files**: `wf-init/lib/state.md`, `wf-init/lib/migrations.md` (new)

**Scope**:
- Extend `build_plan` in state.md with `generated_files[]`, `managed_paths[]`, `approval{}`
- Create migrations.md with schema_version 2→3 and wizard_version 0.6.4→0.6.8 rules
- Document new optional features (routing_abc, decision_ladder, visual_regression, etc.)

**Acceptance criteria**:
- [ ] `build_plan` schema includes all three new fields
- [ ] migrations.md covers all known schema changes
- [ ] Default values for new features are documented
- [ ] No breaking changes to existing state fields

**Estimated effort**: 1-2 hours

---

### WU-2: Create refresher orchestrator

**Files**: `wf-init/lib/refresher.md` (new)

**Scope**:
- Implement phases R-1 through R6 as documented in specification.md
- Each phase is a bash section with clear input/output
- Include error handling and recovery paths
- Use existing helper functions from builder.md

**Acceptance criteria**:
- [ ] All 8 phases (R-1 to R6) implemented
- [ ] Each phase has clear input/output documentation
- [ ] Error handling for each phase
- [ ] Syntax check passes (bash -n)
- [ ] No hardcoded paths (use variables)

**Estimated effort**: 4-6 hours

---

### WU-3: Update Builder to register generated files

**Files**: `wf-init/lib/builder.md`, `wf-init/subagent-builder-core.md`, `wf-init/subagent-builder-heavy.md`, `wf-init/phase8.md`

**Scope**:
- Add SHA256 hash calculation for each generated file
- Populate `state.build_plan.generated_files[]` and `state.build_plan.managed_paths[]`
- Preserve custom AGENTS.md sections with `<!-- WF: DO NOT REGENERATE -->` markers
- Write `.wizard-managed-files.json` in phase8.md

**Acceptance criteria**:
- [ ] Every file written to staging is registered with hash
- [ ] Custom AGENTS.md sections are extracted and re-injected
- [ ] `.wizard-managed-files.json` is created with correct format
- [ ] `.wizard-managed-files.json` is added to .gitignore
- [ ] No changes to existing B1-B8 logic
- [ ] Syntax check passes

**Estimated effort**: 3-4 hours

---

### WU-4: Rewrite wf-refresh command

**Files**: `templates/commands/wf-refresh/_base.md`

**Scope**:
- Remove old Layer 1/2/3 logic
- Replace with calls to refresher.md phases R-1 to R6
- Keep version check and project validation
- Update documentation and examples

**Acceptance criteria**:
- [ ] Old render_template() function removed
- [ ] Manifest download/parsing removed
- [ ] All phases R-1 to R6 called in order
- [ ] Error handling for each phase
- [ ] Syntax check passes
- [ ] Help text updated

**Estimated effort**: 2-3 hours

---

### WU-5: Update wf-cleanup for managed files

**Files**: `templates/commands/wf-cleanup/_base.md`

**Scope**:
- Remove manifest dependency
- Use `.wizard-managed-files.json` for file detection
- Preserve logic for detecting wizard artifacts
- Update documentation

**Acceptance criteria**:
- [ ] Manifest download/parsing removed
- [ ] Uses `.wizard-managed-files.json` if available
- [ ] Falls back to pattern matching if file missing
- [ ] No deletion of user skills
- [ ] Syntax check passes

**Estimated effort**: 1-2 hours

---

### WU-6: Remove manifest generator from CI/CD

**Files**: `.github/workflows/release-please.yml`

**Scope**:
- Remove `update-manifest` job
- Keep release-please release creation
- Keep other CI/CD jobs intact

**Acceptance criteria**:
- [ ] `update-manifest` job removed
- [ ] Release creation still works
- [ ] No other jobs affected
- [ ] Workflow syntax valid

**Estimated effort**: 30 minutes

---

### WU-7: Update documentation

**Files**: `WF_REFRESH_TROUBLESHOOTING.md`, `AI_DEV_WORKFLOW.md`, `README.md`

**Scope**:
- Update refresh flow documentation
- Document new phases R-1 to R6
- Remove manifest-centric troubleshooting
- Add troubleshooting for new phases
- Update README with new refresh behavior

**Acceptance criteria**:
- [ ] All phases documented
- [ ] Troubleshooting covers common errors
- [ ] No references to manifest
- [ ] Examples updated
- [ ] Links are correct

**Estimated effort**: 2-3 hours

---

### WU-8: Integration tests and verification

**Files**: Test scenarios (bash scripts or markdown)

**Scope**:
- Create simulation tests for each scenario:
  1. No-change scenario
  2. Enable feature scenario
  3. Custom content preservation
  4. Deprecation scenario
  5. Migration scenario
- Manual review of diffs
- Verify no user skills deleted
- Verify custom AGENTS.md preserved

**Acceptance criteria**:
- [ ] All 5 scenarios pass
- [ ] No user skills deleted in any scenario
- [ ] Custom AGENTS.md sections preserved
- [ ] Diffs reviewed and approved
- [ ] Commit messages are conventional

**Estimated effort**: 3-4 hours

---

## Implementation order

**Phase 1: Foundation** (WU-1, WU-2)
- Extend state schema and create migrations
- Create refresher orchestrator
- *Checkpoint*: Review and approve before proceeding

**Phase 2: Builder integration** (WU-3)
- Update Builder to register files
- Preserve custom AGENTS.md
- Write managed files
- *Checkpoint*: Review and approve before proceeding

**Phase 3: Command updates** (WU-4, WU-5, WU-6)
- Rewrite wf-refresh command
- Update wf-cleanup
- Remove manifest generator
- *Checkpoint*: Review and approve before proceeding

**Phase 4: Documentation and testing** (WU-7, WU-8)
- Update all documentation
- Run integration tests
- Manual verification
- *Final checkpoint*: All tests pass, diffs reviewed

---

## Dependency graph

```
WU-1 (state schema)
  ↓
WU-2 (refresher)
  ├→ WU-3 (Builder updates)
  │   ├→ WU-4 (wf-refresh command)
  │   └→ WU-5 (wf-cleanup)
  └→ WU-6 (remove manifest job)

WU-4, WU-5, WU-6
  ↓
WU-7 (documentation)
  ↓
WU-8 (testing and verification)
```

## Parallelization

- **WU-1 and WU-2** can be done in sequence (WU-1 is quick)
- **WU-3** depends on WU-1 and WU-2
- **WU-4, WU-5, WU-6** can be done in parallel after WU-3
- **WU-7** can start after WU-4 (documentation)
- **WU-8** is final (testing)

## Rollback points

After each phase, we can rollback:

1. After WU-1, WU-2: No code changes yet; easy rollback
2. After WU-3: Builder changes; can revert if issues found
3. After WU-4, WU-5, WU-6: Command changes; can revert if issues found
4. After WU-7: Documentation only; no code impact
5. After WU-8: Final verification; if issues found, fix and re-test

## Risk mitigation

| Risk | Mitigation |
|------|-----------|
| Builder changes break /wf-init | Review WU-3 carefully; test with existing projects |
| User skills deleted | WU-3 must preserve user skill patterns; WU-8 tests this |
| Custom AGENTS.md lost | WU-3 must implement marker extraction/re-injection; WU-8 tests |
| Manifest removal breaks things | WU-6 removes only job; manifest files kept as artifacts |
| State migration fails | WU-1 must cover all known schema changes; WU-8 tests |

---

## Commit strategy

Each work unit becomes one or more commits:

```
WU-1: "feat: extend state schema for build_plan and migrations"
WU-2: "feat: create wf-init/lib/refresher.md with phases R-1 to R6"
WU-3: "feat: update Builder to register generated files and preserve custom AGENTS.md"
WU-4: "feat: rewrite wf-refresh command to use builder-driven refresh"
WU-5: "feat: update wf-cleanup to use managed files"
WU-6: "ci: remove update-manifest job from release-please.yml"
WU-7: "docs: update refresh flow documentation"
WU-8: "test: add integration tests for refresh scenarios"
```

All commits use conventional commit format and include:
- What changed
- Why it changed
- Files affected
- Testing performed

---

## Success criteria (overall)

- [ ] All 8 work units completed
- [ ] All tests pass
- [ ] No user skills deleted
- [ ] Custom AGENTS.md preserved
- [ ] Diffs reviewed and approved
- [ ] Documentation updated
- [ ] Commits follow conventional format
- [ ] No push until user approval
