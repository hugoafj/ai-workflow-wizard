# State Contract — `.wizard-state.json`

> This file defines the SINGLE source of truth for the wizard state. Every phase reads
> and writes here. No phase should depend on information remembered by the model.
> The wizard must be able to resume even if the conversation is completely lost between
> two phases: the state on disk is enough to know which phase we are in and what was decided.

## Location

`.wizard-state.json` at the **root of the target project** (not in the wizard repo).
It is local to the run and goes in `.gitignore` (same as `.wf-status`).

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

## Schema (schema_version 3)

```json
{
  "schema_version": 3,
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
    "phase45":  { "status": "pending" },
    "phase46":  { "status": "pending" },
    "phase46b": { "status": "pending" },
    "phase47":  { "status": "pending" },
    "phase6":   { "status": "pending" },
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
    "stack": { "primary": null, "framework": null, "detected_from": null },
    "stack_key": null,
    "node_engine": null,
    "npm_major": null,
    "default_branch": null,
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
    "tdd_protocol": null,
    "routing_abc": null,
    "ci": null,
    "cd": null,
    "release_please": null
  },

  "agents": [],

  "sdd": {
    "backend": null,
    "already_initialized": false,
    "refresh_requested": null
  },

  "testing": {
    "runner_detected": null,
    "layers": [],
    "tdd_mode": null,
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
    "e2e_in_ci": false
  },

  "cd": {
    "enabled": null,
    "platform": null,
    "trigger": null,
    "vps_runtime": null,
    "stack_detected": null,
    "deploy_path": null,
    "missing_secrets": []
  },

  "migration": {
    "prior_content_action": null,
    "missing_commands": []
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
  `phase0`, it offers to resume.
- **`discovery.stack_key`**: normalized stack key (e.g. `node-react`, `php-laravel`,
  `python-django`). This is what the Builder uses to select `variants/<stack_key>.md`.
  **Never branch with `if stack === ...`**: the key selects a file.
- **`answers.ides`**: determines which satellites/commands/packed protocols are generated.
- **`testing.tdd_mode`**: `standard` | `strict` → selects `templates/commands/wf-tdd/variants/{standard,strict}.md`.
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
- `wf_state_get '<jq-filter>'` — Read a field from state.
- `wf_state_set '<jq-filter>' '<value>'` — Write a field to state.
- `wf_phase_done <done_phase> <next>` — Mark a phase done and advance pointer.
```

> **IMPORTANT rule**: the initial creation uses `wf_state_init` (cat >). **Updates**
> NEVER use `cat >` or heredocs — always `wf_state_set`/`wf_phase_done` or the IDE's
> `edit` tool. Some IDEs (Windsurf, Cursor) block `cat >` if the file already exists.
>
> **Fallback without `jq`**: if `jq` is not available, the agent edits `.wizard-state.json`
> by reading and rewriting it with its file writing tool (write/edit),
> preserving the rest of the JSON intact. `jq` is the preferred path for determinism.

## Resumption

The orchestrator (`wf-init.md`) on startup:
```bash
if [ -f .wizard-state.json ]; then
  PTR=$(jq -r '.phase_pointer' .wizard-state.json 2>/dev/null)
  echo "Run in progress detected. Current phase: $PTR."
  echo "Resume from $PTR, or restart (deletes .wizard-state.json)? [resume / restart]"
fi
```
