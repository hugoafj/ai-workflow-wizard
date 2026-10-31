# versioned-wizard-state

Branch: `feat/versioned-wizard-state` (from `main` at b05786c, v0.11.2-beta.1). Option A of the team-onboarding analysis, approved by the user.
Engram mirror: project `ai-workflow-wizard`, topic `odd/versioned-wizard-state/tasks`.

## Specs

S1. A teammate who clones a repo with the wizard already initialized must not re-run `/wf-init`. `.wizard-state.json` and `.wizard-managed-files.json` are committed (no longer in `.gitignore`), so `/wf-refresh` and `/wf-cleanup` work in any clone.
S2. The versioned state must hold no machine-specific data. `build_plan.builder_core.scripts` leaked a path relative to the wizard install dir (a session scratchpad under `/private/tmp/...` in the test project) and nothing reads it: stop writing it and strip it from existing states.
S3. The `gentle_ai` block is kept as is (user decision). It describes whoever ran `/wf-init`, is informational only, and no logic outside the init may depend on it.
S4. `/wf-init` recognises an initialized repo (`phase_pointer: done`, or a wizard `AGENTS.md` footer without state) and points to `/wf-onboard` or `/wf-refresh` instead of starting over.
S5. `/wf-refresh` migrates legacy projects: it proposes removing the legacy `.gitignore` entries inside the existing `.gitignore` approval, then commits the state and the manifest. Declining keeps them local and ignored. A fully declined refresh still writes nothing, and a failed commit still rolls everything back.
S6. `/wf-onboard` prepares the teammate's machine without touching the repo: prerequisites, global commands (`install.sh`) and version, dependencies from the lockfile (which activates Husky), the post-commit hook when there is no Husky, MCPs (Windsurf is global only), and real project commands read from the state.
S7. The changes must not break `/wf-refresh`, `/wf-cleanup` or `/wf-init` on what already works (user constraint).

## Tasks

- [x] T1 Origin of the leak (S2). Files: `wf-init/lib/builder-core.py` (drops `scripts`), `wf-init/lib/state-helpers.sh` (`wf_state_sanitize`, exported like the other helpers).
- [x] T2 `/wf-init` (S1, S4). Files: `wf-init/phase8.md` (8.2 no longer ignores the state, 8.3 sanitizes and removes legacy entries, 8.4 marks done before the commit, force-adds both files, verifies them in HEAD, reverts the pointer on failure, 8.6 only checks), `wf-init/phase7.md` (review preview), `templates/commands/wf-init/_base.md` (startup guard), `wf-init/lib/state.md` (location, rule 5, helper list).
- [x] T3 `/wf-refresh` (S5). File: `wf-init/lib/refresher.md`. R5 proposes the legacy-entry removal in the same prompt (prompt text unchanged). R6 snapshot covers both files, writes manifest and state BEFORE staging, sanitizes on promotion, adds both files to the add list and the commit pathspec only when git does not ignore them, and adds a commit-message line.
- [x] T4 `/wf-cleanup` (S7). File: `templates/commands/wf-cleanup/_base.md`. Inventory labels only: Phase 3 already runs `git add -A`, so the deletions are committed.
- [x] T5 `/wf-onboard` (S6). File: `templates/commands/wf-onboard/_base.md`. New phases 0.5, 1.5 and 2.5, Phase 0 checks the versioned files, Phase 3 adds the Windsurf note, Phase 4 reads `discovery.commands`.
- [x] T6 Docs. Files: `AI_DEV_WORKFLOW.md` (architecture, `.gitignore` section, Phase 8, R6 twice, cleanup, section 7.7), `README.md` ("Working in a Team", onboard row, state bullet).
- [x] T7 Verification (S7). Route: inline, scratch repos, nothing run against a real project. See L5 to L8.
- [ ] T8 Review gate and commits. Pending user approval of the full diff (AGENTS.md rule). Planned work units: T1, T2, T3, T4, T5, T6 (see L10).

## Log

L1. Decision: option A (commit the state and the manifest as they are) once the leak is fixed. The user kept the `gentle_ai` values instead of resetting them to null: nothing outside the init reads them, and resetting would break the phase 0 and 0b validations (`gentle_ai.version`, `gentle_ai.doctor` must be non-null) if `/wf-init` restarted.
L2. Evidence from the test project (`demos/tasks-manager/frontend`): `.wizard-managed-files.json` is clean (relative paths, hashes); `.wizard-state.json` leaked only in `build_plan.builder_core.scripts` (2 entries). The fields `builder_core`, `builder_heavy`, `staged_sha256` and `phase_now` have no consumer in the repo.
L3. Found while implementing: `/wf-init` 8.6 ran `wf_phase_done phase8 done` AFTER the commit. With a versioned state that would commit an intermediate pointer and leave the tree dirty. The done mark now happens before the commit and is reverted on failure; 8.6 only checks it.
L4. Found by the R6 harness: summing the two files into `TOTAL_APPROVED` caused a false "approved vs committed" warning in a `.gitignore`-only refresh. Fixed by excluding them from the committed count instead; the original semantics are preserved.
L5. R6 verified by extracting the real block and `refresh-lib.sh` from `refresher.md` into scratch git repos seeded with the test project's state (leak included): legacy migration (both files in HEAD, legacy entries gone, leak stripped, tree clean, no warning); already versioned (second refresh, tree clean); migration declined (nothing written); rejecting pre-commit hook (state, manifest and `.gitignore` restored, tree clean); apply-only (nothing committed, leak stripped).
L6. Also verified in isolation: the startup guard in 4 scenarios, `wf_state_sanitize` (idempotent, tolerates `{}`), the 8.3 `.gitignore` cleanup (including a file left empty), `wf_phase_done` plus revert, the onboard hook install (byte-identical to the Builder's `extract_block` output, second run is a no-op), the version comparison, and `git check-ignore` semantics (tracked files are never reported as ignored). `bash -n` on every modified fenced block: 0 new errors versus `main`.
L7. Not verified: a full `/wf-init` run, `/wf-onboard` inside an IDE, and a clone from a second machine. The wf-onboard fence extraction uses `\140` for the backtick so it does not close the markdown block.
L8. The footer marker `<!-- wf-version: ... -->` is always emitted by `templates/AGENTS.router.md` and already used by `wf-refresh` to detect wizard-managed files, so the guard can rely on it.
L9. Left out on purpose: `.vscode/settings.json` (an auto-approve setting added by VS Code, not part of this work) and `NOTES.md` (the user's notes; the "ignored .wizard-state.json" item is theirs to close after validating).
L10. Size: about 506 changed lines, over the 400-line review threshold. Commit per work unit, with the docs in T6 kept together; consider chained PRs with R6 (T3) reviewed on its own. Known residual risks: merge conflicts in the state (`updated_at`, hashes) when two people refresh in different branches; baseline hashes in a clone reflect whatever was committed; `install.sh` runs from `main` (version pinning is already in NOTES.md).
