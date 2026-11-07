# State Contract — `.wizard-state.json`

> This file defines the SINGLE source of truth for the wizard state. Every phase reads
> and writes here. No phase should depend on information remembered by the model.
> The wizard must be able to resume even if the conversation is completely lost between
> two phases: the state on disk is enough to know which phase we are in and what was decided.

## Location

`.wizard-state.json` at the **root of the target project** (not in the wizard repo).
It is **versioned** (committed in `/wf-init` Phase 8, together with `.wizard-managed-files.json`)
so a teammate who clones the repo reuses it with `/wf-onboard`, `/wf-refresh` and `/wf-cleanup`
instead of re-running `/wf-init`. Only `.wizard-state.json.tmp` and `.wizard-staging/` stay ignored.

## Golden rules

1. **Read before acting**: when entering any phase, the agent reads
   `.wizard-state.json` completely. It assumes nothing from previous turns.
2. **Write before moving forward**: each phase writes its section and updates
   `phase_pointer` BEFORE pausing. If the session dies right after, the next
   session resumes without loss.
3. **Idempotence**: re-executing a phase rewrites only its section; it never corrupts
   the others.
4. **Never knowledge**: only state goes in the state (discovery + user answers +
   pointers). Framework rules are NEVER copied here — they live in
   `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/`.
5. **Shareable**: the state travels in the repo, so it must never hold absolute paths,
   paths relative to the wizard install dir (`WF_DIR`), usernames or session ids. The
   `gentle_ai` block is informational only: it describes the machine of whoever ran
   `/wf-init`, not of whoever cloned the repo, and no logic outside the init may decide
   based on it. `wf_state_sanitize` (state-helpers.sh) strips legacy leaks before a commit.

## Schema (schema_version 4)

```json
{
  "schema_version": 4,
  "wizard_version": "<auto: VERSION file in workflow-wizard>",
  "phase_pointer": "phase0",
  "started_at": "ISO-8601",
  "updated_at": "ISO-8601",

  "phases": {
    "phase0":   { "status": "pending|in_progress|done|skipped" },
    "phase0b":  { "status": "pending" },
    "phase0c":  { "status": "pending" },
    "phase1":   { "status": "pending" },
    "phase2":   { "status": "pending" },
    "phase3":   { "status": "pending" },
    "phase4":   { "status": "pending" },
    "phase5":   { "status": "pending" },
    "phase46":  { "status": "pending" },
    "phase47-cicd": { "status": "pending" },
    "phase6":        { "status": "pending" },
    "phase6a-agents": { "status": "pending" },
    "phase6b-build-heavy": { "status": "pending" },
    "phase7":   { "status": "pending" },
    "phase8":   { "status": "pending" }
  },

  "gentle_ai": {
    "installed": null,
    "version": null,
    "install_choice": null,
    "doctor": null,
    "os": null,
    "warning_incomplete": false
  },

  "discovery": {
    "stack": { "primary": null, "framework": null, "detected_from": null, "stack_key": null, "frontend": null },
    "node_engine": null,
    "npm_major": null,
    "default_branch": null,
    "commands": null,
    "code_files": null,
    "git_commits": null,
    "committers": null,
    "ci_present": null,
    "prior_artifacts": { "agents_md": false, "claude_md": false, "satellites": [], "hook": false },
    "classification": null,
    "conventions": {}
  },

  "answers": {
    "project_name": null,
    "stack_versions": null,
    "ides": [],
    "critical_constraints": []
  },

  "features": {
    "decision_ladder": null,
    "testing": false,
    "ci": null,
    "cd": null,
    "release_please": null
  },

  "agents": [],

  "testing": {
    "runner_detected": null,
    "profile": null,
    "runner": null,
    "runner_existing": null,
    "environment": null,
    "test_pattern": null,
    "test_command": null,
    "frontend_profile": null,
    "frontend_runner": null,
    "frontend_runner_existing": null,
    "frontend_root": null,
    "layers": [],
    "coverage_threshold": null,
    "visual_regression": false,
    "page_object_model": false
  },

  "mcps": [],

  "ci": {
    "ai_reviewer": null,
    "gga_provider": null,
    "gga_modes": [],
    "security_review": null,
    "conventional_commits": null,
    "release_please": null,
    "release_ai_summary": null,
    "release_ai_provider": null,
    "github_remote": null,
    "e2e_in_ci": false,
    "auto_improve": true,
    "inline_suggestions": true
  },

  "cd": {
    "enabled": null,
    "platform": null,
    "trigger": null,
    "vps_runtime": null,
    "stack_detected": null,
    "deploy_path": null,
    "compose_file": null,
    "missing_secrets": []
  },

  "migration": {
    "prior_content_action": null,
    "missing_commands": [],
    "wrap_custom_in_markers": false
  },

  "build_plan": {
    "agents_md": false,
    "satellites": [],
    "commands": [],
    "protocols_flat": [],
    "protocols_skills": [],
    "hook": false,
    "staging_dir": ".wizard-staging",
    "generated_files": [],
    "managed_paths": [],
    "approval": {}
  }
}
```

## Key fields

- **`phase_pointer`**: current phase. On startup, the orchestrator reads it; if it is not
  `phase0`, it offers to resume. Phase 5 advances to `phase6a-agents` (there is no
  `phase6.md` file; `phase6` is a backward-compatible alias). Phase 6b is `phase6b-build-heavy`,
  which advances to `phase7` when complete. Phase 47 is `phase47-cicd` (the old `phase47` key is
  not used).
- **`discovery.stack.stack_key`**: normalized stack key (e.g. `node-react`, `node-nest`,
  `node-generic`, `php-laravel`, `php-generic`, `python-django`). For Node it is `node-<framework>`.
  It comes from `wf_detect_stack` (`state-helpers.sh`): a `composer.json` that requires
  `laravel/framework` gives `php-laravel` even when a `package.json` is also present (a Laravel app
  ships one for its assets); any other `composer.json` gives `php-generic`. This is
  what the Builder uses to select `variants/<stack_key>.md`.
  **Never branch with `if stack === ...`**: the key selects a file.
- **`discovery.stack.framework`**: for Node, the output of `wf_detect_framework`
  (`state-helpers.sh`), derived from `package.json` dependencies, first match wins:
  `nest` | `angular` | `next` | `nuxt` | `vue` | `react` | `express` | `fastify` | `hono` | `koa`
  | `generic` (nothing matched). PHP (`wf_detect_php_framework`, from `composer.json` `require` and
  `require-dev`): `laravel` | `generic`. Other stacks: `django`. Never `null` once phase 1 ran.
- **`testing.profile`**: testing profile resolved from the framework by
  `wf_profile_for_framework`: `react` (react, Vite projects included) | `next` | `vue` (vue, nuxt) | `node-api` (express,
  fastify, hono, koa) | `nest` | `angular` | `generic` | `laravel` | `php`. Selects runner, environment, packages and
  config template. `laravel` and `php` are Composer profiles (`ecosystem: php` in
  `profiles.md`): PHPUnit, no generated unit config, no npm scripts, the command documented is
  the profile's `test_command`. `generic` is a framework token of both ecosystems, so the
  helper takes the stack key's ecosystem (`node` | `php`) as a second argument.
  `null` means a legacy state: for a Node stack the Builder treats it as `react`, the behavior
  every Node project had before profiles existed, and phase 8 picks `laravel` or `php` for a
  PHP `stack_key` instead. R2 fills it from the `stack_key` of the ROOT
  state (the pre-refresh value, not one R1 just rewrote after accepted drift) without overwriting a
  value that is already set, so an installed project never changes its test config as a side effect
  of detection. To change an installed project's profile, set `testing.profile` and re-run
  `/wf-refresh`.
- **`testing.runner`** / **`testing.environment`** / **`testing.test_pattern`**: the runner in
  use (`vitest` | `jest` | `karma` | ...), its test environment (`jsdom` | `node`) and the test
  file convention. When the project already has a configured runner, phase 4.6 records that one
  and sets `testing.runner_existing = true`; otherwise it records the profile default.
  `testing.runner_detected` keeps the raw detection result.
- **`testing.test_command`**: the command that runs the unit and integration tests, copied by phase 4.6
  from the profile's `test_command` (`php artisan test` for Laravel, `vendor/bin/phpunit` for other PHP
  projects). `null` for the Node profiles, whose command is the `test` script (`npm run test`). The
  Builder documents it in AGENTS.md (Testing Approach and the checks before done); editing it here and
  re-running `/wf-refresh` is how a project with a non-standard runner command keeps its own.
- **`discovery.stack.frontend`**: only for a PHP stack: the UI framework of its frontend, from
  `wf_detect_frontend` (`state-helpers.sh`): `react` | `next` | `vue` | `nuxt` | `angular` | `none`. It
  comes from the `package.json` dependencies, never from the mere presence of that file (the Laravel
  skeleton ships one with Vite and axios and no UI); when react and vue are both dependencies, the one
  the sources import wins. `null` for every other stack.
- **`testing.layers`** may also hold `frontend`: the unit tests of the frontend of a PHP project, run with
  the JS profile of `discovery.stack.frontend` next to the PHP runner. It is independent of `unit`.
- **`testing.frontend_profile`** / **`testing.frontend_runner`** / **`testing.frontend_runner_existing`** /
  **`testing.frontend_root`**: the JS profile of that frontend (`wf_profile_for_framework` of
  `discovery.stack.frontend`), its runner, whether the frontend already owns a configured runner (then the
  wizard installs and generates nothing for it), and the folder with its JavaScript sources
  (`wf_detect_frontend_root`; phase 4.6 asks once when none of the usual ones exists). Editing
  `frontend_root` here and re-running `/wf-refresh` is how a non-standard layout is kept.
- **`testing.runner_existing`**: `true` when the project already owns a configured unit runner
  (its dependency AND its config). The wizard then keeps it: the Builder writes no unit config,
  phase 8 installs no unit packages and does not touch the `test` scripts. `null`/`false` means
  the wizard owns the runner (legacy states included, which keeps their previous behavior).
- **Testing profile data**: `templates/protocols/testing/profiles.md` is the single source for what
  each profile installs, generates and documents. The Builder reads it; a new framework is one
  entry there plus its config template.
- **`discovery.commands`**: array of npm script names detected in phase 1. The Builder renders
  the AGENTS.md **Commands** section from it; when absent, the Builder re-detects from
  `package.json` and warns.
- **`discovery.conventions.structure`**: short tree of main folders + purpose (phase 4 reverse
  engineering). Feeds the AGENTS.md **Project Structure** section; when absent the Builder
  falls back to `"flat"`.
- **`answers.ides`**: determines which satellites/commands/packed protocols are generated.
- **`features.testing`**: `true` when the user chose test infrastructure in phase 0c. Gates the
  test-infra phase (`phase46`).
- **`build_plan`**: populated by the Builder with the exact list of artifacts to write.
  - `generated_files[]`: array of `{ path, hash, managed }` for every file written to staging.
  - `managed_paths[]`: array of project-relative paths that the wizard owns (for deletion detection in `/wf-refresh`).
  - `approval{}`: user approvals for adds, updates, deletions (used by `/wf-refresh`).

## Read/write helpers (bash, agnostic)

Every phase uses these patterns. Requires `jq` (fallback documented below).

The implementation lives in `wf-init/lib/state-helpers.sh`, which is a pure bash
file meant to be sourced. Phase files and sub-agents should **not** source this
Markdown file (`state.md`) directly.

```bash
source "$WF_DIR/lib/state-helpers.sh"
```

Available helpers:
- `wf_fetch_version` — Get wizard version from the repo `VERSION` file (fallback: local `VERSION`, GitHub releases/tags); normalized, no `v` prefix.
- `wf_state_init` — Initialize `.wizard-state.json` if it doesn't exist.
- `wf_sha256 <file>` — Compute SHA256 hash of a file (portable macOS/Linux fallback).
- `wf_state_get '<jq-filter>'` — Read a field from state.
- `wf_state_set '<jq-filter>' '<value>'` — Write a field to state. Values are passed safely via `jq --arg`, so:
  - Strings: `wf_state_set '.field' "value"` (no escaping needed, jq handles it)
  - Booleans: `wf_state_set '.field' "true"` (pass as string, jq parses it)
  - Numbers: `wf_state_set '.field' "42"` (pass as string, jq parses it)
  - JSON structures: `wf_state_set '.field' "[item1,item2]"` (pass valid JSON as string, jq parses it)
  - Null: `wf_state_set '.field' "null"` (pass as string, jq parses it)
- `wf_phase_done <done_phase> <next>` — Mark a phase done and advance pointer.
- `wf_state_sanitize` — Strip machine-specific data (legacy `build_plan.builder_core.scripts`) before the state is committed. Idempotent.
```

> **IMPORTANT rule**: the initial creation uses `wf_state_init` (cat >). **Updates**
> NEVER use `cat >` or heredocs — always `wf_state_set`/`wf_phase_done` or the IDE's
> `edit` tool. Some IDEs (Windsurf, Cursor) block `cat >` if the file already exists.
>
> **Fallback without `jq`**: if `jq` is not available, the agent edits `.wizard-state.json`
> by reading and rewriting it with its file writing tool (write/edit),
> preserving the rest of the JSON intact. `jq` is the preferred path for determinism.

## Resumption

The orchestrator (the `/wf-init` skill, `templates/commands/wf-init/_base.md`) on startup:
```bash
if [ -f .wizard-state.json ]; then
  PTR=$(jq -r '.phase_pointer' .wizard-state.json 2>/dev/null)
  echo "Run in progress detected. Current phase: $PTR."
  echo "Resume from $PTR, or restart (deletes .wizard-state.json)? [resume / restart]"
fi
```
