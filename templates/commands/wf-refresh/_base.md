# /wf-refresh — Builder-driven refresh

⚡ **AUTOMATION**: Phases R-1 and R0 run automatically. Phases R1–R6 are interactive (you approve changes before applying).

---

> Deterministic refresh that re-runs the Builder to detect and apply changes to your project.
> Replaces the old Layer 1/2/3 approach with a single source of truth: the Builder.
> Works as a complement to `/wf-init`. Assumes /wf-init already ran in this repo before.
>
> Source: github.com/hugoafj/ai-workflow-wizard

## What this refresh does

Detects project drift and applies updates safely:

1. **Phase R-1**: Update global commands (`wf-init`, `wf-refresh`, `wf-cleanup`) if outdated
2. **Phase R0**: Validate `.wizard-state.json` and detect active IDEs
3. **Phase R1**: Re-discover project (stack, node engine, etc.) and detect drift
4. **Phase R2**: Migrate state schema and ask about new optional features
5. **Phase R3**: Re-run Builder (B1-B9) to generate all artifacts into `.wizard-staging/`
6. **Phase R4**: Compare staging with project using SHA256 hashes; classify files as add/update/delete/unchanged
7. **Phase R5**: Show grouped diff and collect your approvals
8. **Phase R6**: Apply approved changes, update state, commit, clean staging

---

## How /wf-refresh works

**Automation + Human guidance**:
- **Phases R-1 & R0** (automated): Execute version checks and validations automatically
- **Phases R1–R6** (interactive): Analyze and propose changes; pause for user approval

**Your role as the agent**:

1. **Execute Phase R-1** (global command refresh): Check versions, propose update if needed
2. **Execute Phase R0** (validation): Verify `.wizard-state.json` exists and is valid
3. **Execute Phases R1–R6** in sequence, pausing for user approval at Phase R5

**Inviolable rules**:

1. Do NOT apply changes without explicit user OK at Phase R5
2. Do NOT `git add` or `git commit` until Phase R6 (after approvals)
3. Show clear diffs before applying any changes
4. Respect content marked with `<!-- WF: DO NOT REGENERATE -->`
5. Never delete user skills or custom content without explicit approval
6. If a user response is ambiguous, ask again

---

## Implementation

Download the refresh orchestrator and supporting files, then read and execute each phase in `refresher.md` in order. **Do NOT `source` Markdown files** — read them as instructions and execute the fenced bash blocks one at a time.

```bash
#!/bin/bash
set -e

# Verify .wizard-state.json exists
if [[ ! -f .wizard-state.json ]]; then
  echo "✗ .wizard-state.json not found"
  echo "  Please run /wf-init first"
  exit 1
fi

# Wizard repository
WIZARD_REPO="hugoafj/ai-workflow-wizard"
WIZARD_BRANCH="main"
WF_RAW="https://raw.githubusercontent.com/${WIZARD_REPO}/${WIZARD_BRANCH}"

# Local directory for downloaded refresh files (temporary, can be cleaned later)
WF_DIR="/tmp/wf-refresh-phases"
mkdir -p "$WF_DIR"
mkdir -p "$WF_DIR/lib"

echo "Downloading refresh files from GitHub..."
echo "Source: ${WIZARD_REPO}@${WIZARD_BRANCH}/wf-init/"

curl -fsSL "${WF_RAW}/wf-init/lib/refresher.md" > "${WF_DIR}/lib/refresher.md"
curl -fsSL "${WF_RAW}/wf-init/lib/state.md" > "${WF_DIR}/lib/state.md"
curl -fsSL "${WF_RAW}/wf-init/lib/state-helpers.sh" > "${WF_DIR}/lib/state-helpers.sh"
curl -fsSL "${WF_RAW}/wf-init/lib/builder.md" > "${WF_DIR}/lib/builder.md"
curl -fsSL "${WF_RAW}/wf-init/subagent-builder-core.md" > "${WF_DIR}/subagent-builder-core.md"
curl -fsSL "${WF_RAW}/wf-init/subagent-builder-heavy.md" > "${WF_DIR}/subagent-builder-heavy.md"
curl -fsSL "${WF_RAW}/wf-init/phase6a-agents.md" > "${WF_DIR}/phase6a-agents.md"
curl -fsSL "${WF_RAW}/wf-init/phase6b-build-heavy.md" > "${WF_DIR}/phase6b-build-heavy.md"
mkdir -p "${WF_DIR}/temp-files"
curl -fsSL "${WF_RAW}/temp-files/AGENTS.md" > "${WF_DIR}/temp-files/AGENTS.md" 2>/dev/null || true

if [ ! -s "${WF_DIR}/lib/refresher.md" ]; then
  echo "✗ Could not download refresher.md from GitHub"
  exit 1
fi

echo "✓ Refresh files downloaded to: ${WF_DIR}"
```

Now read the orchestrator and execute each phase in order:

**Next step**: open `${WF_DIR}/lib/refresher.md` and execute the bash blocks under each **Phase** heading in sequence, pausing for user approval at Phase R5.

---

## Troubleshooting

### Phase R-1 fails (global command update)

- **Issue**: `install.sh` not found or fails
- **Solution**: Run `install.sh` manually or skip the update (you can run it later)

### Phase R0 fails (validation)

- **Issue**: `.wizard-state.json` missing or invalid
- **Solution**: Run `/wf-init` first to initialize the project

### Phase R1 fails (project drift)

- **Issue**: Discovery commands fail
- **Solution**: Check that `package.json`, `git`, and other project files are accessible

### Phase R2 fails (state migration)

- **Issue**: Schema migration fails
- **Solution**: Run `/wf-cleanup` and `/wf-init` to reset the project

### Phase R3 fails (Builder)

- **Issue**: Builder fails to generate staging
- **Solution**: Check `.wizard-state.json` for validity; may need `/wf-cleanup` + `/wf-init`

### Phase R5 (review gate)

- **Issue**: Diff looks wrong or incomplete
- **Solution**: Review the diff carefully; you can reject changes and re-run `/wf-refresh` later

### Phase R6 fails (apply)

- **Issue**: Git operations fail
- **Solution**: Check git status; may need to commit or stash changes first

---

## Key concepts

### Hash-based diff

Each file in staging is compared with the project using SHA256 hashes:
- **Unchanged**: Hash matches → file is skipped (not re-copied)
- **Updated**: Hash differs → file is proposed for update
- **Added**: File only in staging → proposed for addition
- **Deleted**: File only in project and marked as wizard-managed, unchanged → proposed for deletion
- **Deleted-modified**: File in old `managed_paths`, not in new staging, but project hash differs from recorded hash → flagged for explicit approval

### Wizard-managed files

Files that the wizard owns and can manage:
- `wf-*/SKILL.md` (wizard skills)
- `.agents/skills/wf-*` (universal wizard skills)
- `.claude/skills/wf-*`, `.cursor/skills/wf-*`, etc. (per-IDE wizard skills)
- `.agents/protocols/wf-*` (wizard protocols)
- `.github/workflows/release-please.yml`, `.github/workflows/quality-guard.yml`, etc.
- `.husky/post-commit`, `.husky/commit-msg`
- `AGENTS.md`, `vitest.config.ts`, `playwright.config.ts`, etc.

User skills and custom content are never deleted.

### Custom AGENTS.md preservation

Sections inside `<!-- WF: DO NOT REGENERATE -->` markers are preserved:

```markdown
# AGENTS.md — my-project

<!-- WF: DO NOT REGENERATE -->
## Custom section

This section is maintained by me and will not be overwritten by /wf-refresh.
<!-- /WF: DO NOT REGENERATE -->

## Wizard-managed section

This section is regenerated by /wf-refresh.
```

---

## Next steps

After refresh completes:

1. Review the commit: `git log -1 -p`
2. If satisfied: `git push` (when ready)
3. If issues: `git revert HEAD` and re-run `/wf-refresh`

---

## Related commands

- `/wf-init` — Initialize a new project with the wizard
- `/wf-cleanup` — Remove all wizard artifacts and reset the project
- `/wf-settings` — Configure wizard options
