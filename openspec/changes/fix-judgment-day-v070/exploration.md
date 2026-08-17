# Exploration: v0.7.0-beta.1 critical fixes (Judgment Day findings)

## Current State

The `v0.7.0-beta.1` release merged the builder-driven `/wf-refresh` refactor (`refactor-wf-refresh-builder-driven`). A post-merge `judgment-day` review between `v0.6.6-beta.1` and `v0.7.0-beta.1` found the release is not deployable/usable in several ways:

1. **`/wf-refresh` is not executable.**
   - `templates/commands/wf-refresh/_base.md` calls `source wf-init/lib/refresher.md` as a shell script.
   - `install.sh` and `wf-init` do not download `wf-init/lib/refresher.md` or `wf-init/lib/migrations.md` into the target project.
   - Even if present, `source`ing a Markdown file (with prose, headings, tables, fenced code blocks) is not valid bash.
   - `refresher.md` also tries `source wf-init/subagent-builder-core.md` and `source wf-init/subagent-builder-heavy.md`; those are sub-agent prompts, not bash scripts.

2. **Wizard version migration is hardcoded and compared lexicographically.**
   - `migrations.md` and `refresher.md` hardcode `0.6.8-beta` as the migration target.
   - `refresher.md` uses `[[ "$WIZARD_VERSION" < "0.6.8-beta" ]]` (ASCII string comparison), which fails for semver: e.g. `0.10.0` is treated as `< 0.6.8` and `0.6.10` is also treated as `< 0.6.8`.
   - `test-scenarios.md` expects `wizard_version == "0.6.8-beta"`.
   - `VERSION` file, `AGENTS.md` footer, and release tag (`0.7.0-beta.1`) are inconsistent.

3. **`AGENTS.md` contradicts the implemented feature set.**
   - Footer says `ladder=no, tdd=no, routing=no` and claims no agent protocols.
   - `builder.md` and `AGENTS.router.md` generate/enable `wf-ladder`, `wf-tdd`, `wf-orchestrator`, and `wf-sdd-trigger`.
   - Commands table omits those four commands while `wf-cleanup` knows to remove them.

4. **`AI_DEV_WORKFLOW.md` / `WF_REFRESH_TROUBLESHOOTING.md` describe the old model.**
   - Still mention `.wizard-manifests/` (removed), old Layer 1/2/3 refresh, and `wf-version: 0.1.0-beta.1`.
   - Refresh troubleshooting claims diff behavior that `refresher.md` does not implement.

5. **Preservation and deletion-safety are incomplete.**
   - Custom `AGENTS.md` sections are extracted but never re-injected (`refresher.md` Phase R3 comment).
   - Files in old `managed_paths` whose hash changed are silently ignored instead of classified as `deleted_modified` requiring explicit approval.
   - `.wizard-managed-files.json` is generated differently by `refresher.md` and `phase8.md`.
   - `wf-cleanup` does not remove `.wizard-managed-files.json` even though docs say it should.

## Affected Areas

| File | Why affected |
|------|-------------|
| `templates/commands/wf-refresh/_base.md` | Calls `source` on Markdown library files; must be an agent instruction flow. |
| `wf-init/lib/refresher.md` | Mixed agent instructions and bash blocks; uses `source` on prompts; hardcoded version; incomplete preservation/deletion logic. |
| `wf-init/lib/migrations.md` | Hardcodes `0.6.8-beta` as target; contains prose that bash cannot execute. |
| `wf-init/lib/state.md` | Labels schema as v2 but already includes v3 fields (`generated_files`, `managed_paths`, `approval`). |
| `wf-init/lib/builder.md` | Commands table and feature flags must match `AGENTS.md`. |
| `templates/AGENTS.router.md` | Placeholder `{{discovery.commands}}` / `{{features.*_yesno}}` not defined in state. |
| `AGENTS.md` | Footer and features table are stale; must reflect builder-driven routing and commands. |
| `AI_DEV_WORKFLOW.md` | Mentions deprecated `.wizard-manifests/`, old refresh layers, stale footer example. |
| `WF_REFRESH_TROUBLESHOOTING.md` | Describes diff behavior not implemented in `refresher.md`. |
| `templates/commands/wf-cleanup/_base.md` | Must remove `.wizard-managed-files.json`. |
| `VERSION` | Should match the release tag `0.7.0-beta.1`. |
| `test-scenarios.md` (openspec SDD) | Hardcoded version expectation must be updated. |

## Approaches

### Option A: Convert `/wf-refresh` to agent-instruction workflow (recommended)

Rewrite `wf-refresh/_base.md` to download `refresher.md` (and related phase files) into a temporary directory and present it to the agent as instructions, exactly like `wf-init` does with `phase*.md`. The agent executes bash blocks selectively. Builder phases are delegated to the same sub-agent prompts used by `wf-init`.

- Pros: consistent with `wf-init`; no need to maintain two execution modes; Markdown files stay readable as docs/instructions.
- Cons: requires more agent turns; `/wf-refresh` becomes a multi-step conversation.

### Option B: Convert library files to pure `.sh` scripts

Rename `refresher.md` and `migrations.md` to `.sh`, strip all prose, and download them as real shell scripts. `wf-refresh/_base.md` then `source`s real shell.

- Pros: `source` works as written; fewer agent turns.
- Cons: loses the documentation/instruction duality of the project; breaks the SDD artifact format; requires rewriting many files; sub-agent prompts (`subagent-builder-*.md`) cannot become shell scripts.

### Option C: Minimal patch to make `source` not fail

Keep `source` but wrap every Markdown prose line in shell comments or skip non-code blocks.

- Pros: smallest change.
- Cons: fragile; every edit to `refresher.md` can break execution; still does not solve missing downloads or sub-agent delegation.

## Recommendation

Use **Option A**. It aligns `/wf-refresh` with `/wf-init`: Markdown files are agent instructions, not shell scripts, and the Builder is invoked through the same sub-agent prompts.

For version migrations, replace the hardcoded target with a cumulative migration list and a semver comparison function, writing the actual `TARGET_VERSION` (from the wizard's `VERSION` file or remote) into state.

For documentation, treat `AGENTS.md` and `AI_DEV_WORKFLOW.md` as first-class artifacts that must be regenerated/updated by the Builder when commands or features change.

## Risks

- Changing `/wf-refresh` execution model may break the current SDD test scenarios; they must be updated and re-run.
- The fix touches many files, so the PR will be large unless split into work units.
- `AGENTS.md` footer and feature flags are generated by the Builder; a single source of truth must be defined.

## Ready for Proposal

Yes. The Judgment Day findings provide enough evidence to scope the proposal.
