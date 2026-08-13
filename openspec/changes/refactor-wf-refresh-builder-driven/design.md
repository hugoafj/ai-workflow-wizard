# Design: Refactor `/wf-refresh` to builder-driven migration

**Change**: `refactor-wf-refresh-builder-driven`  
**Status**: Design  
**Created**: 2026-08-13

## Architecture overview

```
User runs /wf-refresh
    ↓
Phase R-1: Global command refresh
    ↓
Phase R0: Project validation
    ↓
Phase R1: Project content drift (re-discovery)
    ↓
Phase R2: State/schema migration
    ↓
Phase R3: Builder re-run (B1-B9) → .wizard-staging/
    ↓
Phase R4: Hash-based diff (add/update/delete/unchanged)
    ↓
Phase R5: Review gate (user approvals)
    ↓
Phase R6: Apply and close (copy files, commit, clean)
    ↓
Done (no push)
```

## Data flow

### Input state
```
.wizard-state.json (schema_version 2 or 3)
├── discovery.* (stack, node_engine, etc.)
├── answers.* (project_name, ides, etc.)
├── features.* (ladder, tdd, routing, ci, cd, release)
├── testing.* (layers, tdd_mode, coverage, etc.)
├── ci.* (ai_reviewer, gga_modes, etc.)
├── build_plan (from previous /wf-init or /wf-refresh)
└── ... other fields
```

### Processing pipeline
```
Phase R-1: Update global commands (if needed)
    ↓
Phase R0: Validate state, detect IDEs
    ↓
Phase R1: Re-discover project → update discovery.* in state
    ↓
Phase R2: Migrate schema (v2→v3), ask about new features
    ↓
Phase R3: Run Builder with updated state
    ├── B1-B6: Generate protocols, AGENTS.md, satellites
    ├── B7-B9: Generate commands, hooks, CI/CD
    └── Register generated_files and managed_paths in state
    ↓
Phase R4: Compare staging vs project by hash
    ├── For each file: calculate SHA256
    ├── Classify: add/update/delete/unchanged
    └── Build refresh-plan.json
    ↓
Phase R5: Present diff, collect user approvals
    ├── Ask: Apply added? [yes/no]
    ├── Ask: Apply updated? [yes/no]
    └── Ask: Delete removed? [yes/no]
    ↓
Phase R6: Apply approved changes
    ├── Copy adds/updates from staging
    ├── Delete approved removals
    ├── Update state and .wizard-managed-files.json
    ├── Commit with conventional message
    └── Clean staging
    ↓
Output state
```

### Output state
```
.wizard-state.json (schema_version 3)
├── wizard_version: "0.6.8-beta.1" (updated)
├── discovery.* (updated from Phase R1)
├── answers.* (unchanged or updated if user approved)
├── features.* (unchanged or updated if user enabled new features)
├── build_plan (updated with new generated_files and managed_paths)
└── ... other fields

.wizard-managed-files.json (new)
├── wizard_version: "0.6.8-beta.1"
├── generated_at: "ISO-8601"
└── files: [ { path, hash, managed: true }, ... ]
```

## File structure

### New files to create

```
wf-init/lib/refresher.md
├── Phase R-1: Global command refresh
├── Phase R0: Project validation
├── Phase R1: Project content drift
├── Phase R2: State/schema migration
├── Phase R3: Build new staging
├── Phase R4: Diff and plan
├── Phase R5: Review gate
└── Phase R6: Apply and close

wf-init/lib/migrations.md
├── Migration rules by schema_version
├── Migration rules by wizard_version
└── Default values for new fields

templates/commands/wf-refresh/_base.md (rewritten)
├── Phase -1: Version check (existing)
├── Phase 0: Validation (existing)
├── Phase 1-6: Call refresher.md phases
└── Phase 7: Commit and close
```

### Modified files

```
wf-init/lib/state.md
├── Extend build_plan schema
│   ├── Add generated_files[]
│   ├── Add managed_paths[]
│   └── Add approval{}
└── Bump schema_version to 3

wf-init/lib/builder.md
├── Step B9: Register generated files
│   ├── Calculate SHA256 for each file
│   ├── Populate build_plan.generated_files
│   └── Populate build_plan.managed_paths
└── Custom AGENTS.md preservation
    ├── Extract <!-- WF: DO NOT REGENERATE --> sections
    └── Re-inject after generation

wf-init/subagent-builder-core.md
├── Record files in build_plan as written to staging
└── Preserve custom AGENTS.md markers

wf-init/subagent-builder-heavy.md
├── Record files in build_plan as written to staging
└── Register CI/CD and command files

wf-init/phase8.md
├── Write .wizard-managed-files.json
├── Add to .gitignore
└── Keep existing staging cleanup

templates/commands/wf-refresh/_base.md
├── Remove old Layer 1/2/3 logic
├── Call refresher.md phases R-1 to R6
└── Keep version check and validation

templates/commands/wf-cleanup/_base.md
├── Remove manifest dependency
└── Use managed_paths for detection

.github/workflows/release-please.yml
├── Remove update-manifest job
└── Keep release-please release creation

WF_REFRESH_TROUBLESHOOTING.md
├── Update guidance
└── Remove manifest-centric troubleshooting

AI_DEV_WORKFLOW.md
├── Update refresh flow documentation
└── Document new phases R-1 to R6
```

## Key algorithms

### Hash-based diff (Phase R4)

```python
def build_diff_plan(staging_dir, project_root, old_managed_paths, old_managed_files):
    plan = {
        "added": [],
        "updated": [],
        "deleted": [],
        "unchanged": [],
        "deleted_modified": []
    }
    
    # Scan staging
    for file_path in walk(staging_dir):
        staging_hash = sha256(read(staging_dir / file_path))
        project_path = project_root / file_path
        
        if project_path.exists():
            project_hash = sha256(read(project_path))
            if staging_hash == project_hash:
                plan["unchanged"].append({ path: file_path, hash: staging_hash })
            else:
                plan["updated"].append({
                    path: file_path,
                    old_hash: project_hash,
                    new_hash: staging_hash
                })
        else:
            plan["added"].append({ path: file_path, hash: staging_hash })
    
    # Scan old managed paths
    for old_path in old_managed_paths:
        project_path = project_root / old_path
        if project_path.exists() and old_path not in staging_files:
            old_hash = old_managed_files.get(old_path)
            current_hash = sha256(read(project_path))
            
            if old_hash == current_hash:
                plan["deleted"].append({
                    path: old_path,
                    hash: old_hash,
                    reason: "deprecated"
                })
            else:
                plan["deleted_modified"].append({
                    path: old_path,
                    old_hash: old_hash,
                    current_hash: current_hash
                })
    
    return plan
```

### Custom AGENTS.md preservation

```python
def preserve_custom_agents_md(project_root, staging_dir):
    project_agents = project_root / "AGENTS.md"
    staging_agents = staging_dir / "AGENTS.md"
    
    if not project_agents.exists():
        return  # No custom content to preserve
    
    # Extract custom sections
    custom_sections = []
    in_custom = False
    for line in read(project_agents).split("\n"):
        if "<!-- WF: DO NOT REGENERATE -->" in line:
            in_custom = True
        elif "<!-- /WF: DO NOT REGENERATE -->" in line:
            in_custom = False
        elif in_custom:
            custom_sections.append(line)
    
    if not custom_sections:
        return  # No custom sections to preserve
    
    # Re-inject into generated AGENTS.md
    generated = read(staging_agents)
    
    # Find insertion point (after first ## heading)
    lines = generated.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("## "):
            insert_idx = i + 1
            break
    
    # Insert custom sections
    lines.insert(insert_idx, "<!-- WF: DO NOT REGENERATE -->")
    lines.extend(custom_sections)
    lines.insert(insert_idx + len(custom_sections) + 1, "<!-- /WF: DO NOT REGENERATE -->")
    
    write(staging_agents, "\n".join(lines))
```

### Wizard-managed file detection

```python
def is_wizard_managed(path):
    """Determine if a file is managed by the wizard."""
    
    # Explicit patterns
    patterns = [
        "wf-*/SKILL.md",           # Wizard skills
        ".agents/skills/wf-*",     # Universal wizard skills
        ".claude/skills/wf-*",     # Per-IDE wizard skills
        ".cursor/skills/wf-*",
        ".windsurf/skills/wf-*",
        ".devin/skills/wf-*",
        ".kiro/skills/wf-*",
        ".codex/skills/wf-*",
        ".agents/protocols/wf-*",  # Wizard protocols
        ".github/workflows/release-please.yml",
        ".github/workflows/quality-guard.yml",
        ".github/workflows/security-review.yml",
        ".github/workflows/deploy.yml",
        ".husky/post-commit",
        ".husky/commit-msg",
        ".commitlintrc.json",
        "vitest.config.ts",
        "playwright.config.ts",
        "AGENTS.md",
        ".gga",
        ".pr_agent.toml",
        "release-please-config.json",
        ".release-please-manifest.json"
    ]
    
    for pattern in patterns:
        if fnmatch(path, pattern):
            return True
    
    return False
```

## Error handling strategy

### Graceful degradation

| Phase | Error | Action |
|-------|-------|--------|
| R-1 | install.sh fails | Warn, continue with local version |
| R-1 | Remote VERSION unreachable | Warn, use local version |
| R0 | .wizard-state.json missing | STOP, ask user to run /wf-init |
| R0 | schema_version < 2 | STOP, state too old |
| R1 | Discovery commands fail | Warn, keep existing discovery |
| R2 | Migration fails | STOP, ask user to run /wf-cleanup + /wf-init |
| R3 | Builder fails | STOP, show error |
| R4 | Staging is empty | STOP, Builder failed |
| R5 | User rejects all | Abort, no changes |
| R6 | git operations fail | STOP, preserve state |
| R6 | Runtime setup fails | Warn, user can run manually |

### Recovery paths

1. **If Phase R-1 fails**: User can run `install.sh` manually later
2. **If Phase R0 fails**: User must run `/wf-init` first
3. **If Phase R2 fails**: User must run `/wf-cleanup` + `/wf-init`
4. **If Phase R3 fails**: Check `.wizard-state.json` validity; may need `/wf-cleanup` + `/wf-init`
5. **If Phase R5 user rejects**: No changes applied; user can re-run `/wf-refresh` later
6. **If Phase R6 git fails**: State preserved; user can manually commit or re-run

## Performance considerations

### Optimization opportunities (deferred to iteration 2)

1. **Pre-flight check** (Opción C): Download manifest of template hashes; skip Builder if nothing changed
2. **Incremental Builder** (Opción B): Only regenerate files whose dependencies changed
3. **Parallel file operations**: Copy multiple files in parallel during Phase R6

### Current approach (Opción A)

- Full Builder re-run: ~5-10 seconds (acceptable for refresh frequency)
- Hash-based diff: O(n) where n = number of generated files (~100-200)
- Staging cleanup: ~1 second

## Testing strategy

### Unit tests (bash -n)

- Syntax check all new bash snippets in refresher.md
- Syntax check all modified phases in phase8.md

### Integration tests (simulation)

1. **No-change scenario**: `/wf-refresh` on 0.6.8-beta project with no changes → no diff
2. **Enable feature**: Change `features.decision_ladder` to true → adds wf-ladder files
3. **Custom content**: Add custom AGENTS.md section with markers → preserved after refresh
4. **Deprecation**: Simulate removed file → proposed for deletion
5. **Migration**: Run `/wf-refresh` on 0.6.4-beta project → migrates schema, updates state

### Manual review

- Review all diffs before commit
- Verify no user skills are deleted
- Verify custom AGENTS.md sections are preserved
- Verify commit message is conventional

## Rollback strategy

If issues are discovered after commit:

1. **Revert commit**: `git revert <commit-hash>`
2. **Restore previous state**: `.wizard-state.json` and `.wizard-managed-files.json` are in git history
3. **Re-run `/wf-init`** if needed: `/wf-cleanup` + `/wf-init`

---

## Next steps

1. **Tasks phase**: Break into reviewable work units
2. **Apply phase**: Implement files and changes
3. **Verify phase**: Run tests and manual review
