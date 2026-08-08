# Builder — deterministic assembly (Phase 6 + writing Phase 8)

> **⚠️ RUN THIS NOW.** Do not ask if the user wants to continue.
> Do not say it is "too long". Do not suggest using another IDE. Simply read
> and execute each step in order. It is mechanical: read, resolve, write.
>
> **It is not a gentle-ai skill.** It has no complex internal logic. These are
> simple instructions that any agent can execute step by step.

<!--
  The Builder does NOT make decisions (constraint 6). It assembles artifacts
  deterministically from `.wizard-state.json` + the templates at `$WF_ROOT/templates/`.
  It is mechanical code/procedure, not free generation. It replaces the old
  phases 6a-6d ("generate in memory") and the Phase 8 writing: now it writes to a
  STAGING directory on disk, not to memory.

  Language agnosticism rule (constraint 9): every stack-based selection is
  "choose the variants/<stack_key>.md file". There are NEVER `if stack == "php"` branches.
-->

## Inputs

- `.wizard-state.json` (state; see `lib/state.md`).
- `$WF_ROOT/templates/` from the wizard repo (single source of knowledge and templates).

## Output

- Staging at `state.build_plan.staging_dir` (default `.wizard-staging/`) within the
  target project directory. Phase 7 displays it by reading from disk; Phase 8 promotes it to
  its final destination. Nothing lives "in memory".

## Procedure (deterministic)

> **⚠️ UNIVERSAL EXTRACTION RULE**: ALL template files
> (`.tmpl.md`, `.yml.md`, `.json.md`, or any `.md` in `$WF_ROOT/templates/`)
> may contain code wrapped in markdown code blocks (```` ```yaml ````,
> ```` ```json ````, ```` ```typescript ````). When writing a target
> file (`.ts`, `.json`, `.yaml`, `.yml`, etc.), extract ONLY the content
> from INSIDE the code block, without the markdown comments, instructions
> "Generate `filename`:", or the backtick fencing.
>
> **Template formats and how to extract them**:
> - `.tmpl.md` → extract from ```` ```typescript ````, ```` ```yaml ````, or ```` ```bash ````
> - `.yml.md` / `.json.md` in `variants/` → extract from ```` ```yaml ```` or ```` ```json ````
> - `.md` without code fence → use the file AS-IS (raw content, but strip `#` prose header lines if they exist)
>
> **Target types**:
> - **Standalone file** (content is written as-is): `.yml`, `.json`, `.ts`, `.sh`
> - **Fragment** (injected into an existing file): `ai-summary-job`, `coverage-thresholds`,
>   `test-scripts`, `e2e-scripts`, `playwright-mcp.settings`. These are NOT written as
>   separate files — they are merged into the target file.
>
> **Content resolution**:
> - **Pseudo-conditionals** (`<if ...>:`) inside the code fence → resolve based on state before writing
> - **Placeholders** (`<provider>`, `<version>`, `<patterns>`) → resolve from state or stop if missing
> - **chmod +x** for hooks → apply after writing the file
>
> **NEVER** write the entire markdown content (prose + backticks) into the target file.

### Step B1 — Load state
Read `.wizard-state.json` completely. If any required field for an artifact is missing,
STOP and report (do not invent defaults).

### Step B2 — Resolve selection keys
- `STACK=$(jq -r '.discovery.stack_key' .wizard-state.json)`
- `IDES=$(jq -r '.answers.ides[]' .wizard-state.json)`
- `TDD_MODE=$(jq -r '.testing.tdd_mode' .wizard-state.json)`
- `LAYERS=$(jq -r '.testing.layers[]' .wizard-state.json)`
- `LADDER=$(jq -r '.features.decision_ladder' .wizard-state.json)`
- `TDD=$(jq -r '.features.tdd_protocol' .wizard-state.json)`
- `ROUTING=$(jq -r '.features.routing_abc' .wizard-state.json)`
- `CICD=$(jq -r '.features.ci' .wizard-state.json)`
- `CD=$(jq -r '.features.cd' .wizard-state.json)`
- `RELEASE=$(jq -r '.features.release_please' .wizard-state.json)`
- `BACKEND=$(jq -r '.sdd.backend' .wizard-state.json)`
- `AUTO_IMPROVE=$(jq -r '.ci.auto_improve // true' .wizard-state.json)`
- `INLINE_SUGGESTIONS=$(jq -r '.ci.inline_suggestions // true' .wizard-state.json)`

### Step B3 — Assemble protocol bodies (single source → final body)
For each active protocol, build its BODY once:

```
build_protocol_body(name):
  body = content of $WF_ROOT/templates/protocols/<name>/_base.md   # without the internal header comment
  # insert stack variant if it exists and applies
  if exists $WF_ROOT/templates/protocols/<name>/variants/<STACK>.md:
    body = body with the variant marker replaced by that file
  # special case tdd: variant by mode, not by stack
  if name == "tdd":
    replace {{TDD_MODE_VARIANT}} with variants/<TDD_MODE>.md
  return body
```

Special case — this wizard's own protocols (`wf-ladder`, `wf-sdd-trigger`, `wf-orchestrator`;
replaces the old, retired `decision-ladder` bundle — see `AI_DEV_WORKFLOW.md` §6.3 for the
naming/scope rationale). Three independent protocols, NEVER split or summarize their bodies:
- `wf-sdd-trigger` is MANDATORY only if `ROUTING == true` (state field kept as `features.routing_abc`
  for backward compatibility with existing `.wizard-state.json` files — it now means "this
  project's own SDD-forcing policy is active", not "Routes A/B/C"). Decides `wf-no-sdd` vs
  `wf-force-sdd`, emits `wf-preflight`, and waits for user confirmation. It NEVER specifies HOW
  gentle-ai delegates/routes — that stays gentle-ai's own native content per adapter.
- `wf-ladder` (7 rungs) is OPTIONAL: included only if `LADDER == true` (state field kept as
  `features.decision_ladder`).
- `wf-orchestrator` (single entry point) is built whenever `ROUTING == true` OR `LADDER == true`
  — it never duplicates their content, it only sequences which of them (plus `wf-tdd`) apply.
- If both `ROUTING` and `LADDER` are false: none of the three are built.

Protocols to build (conditional by features):
- `wf-orchestrator`, `wf-ladder`, `wf-sdd-trigger`: per the rules above.
- `tdd` (packaged as skill `wf-tdd`): if `TDD == true` AND `LAYERS` is not empty (variant = `TDD_MODE`).
- `sdd` (packaged as skill `wf-sdd-config`): always when `BACKEND != null`.
- `architecture`: always.
- (`testing`, `cicd`, `ides`, `commands`, `workflow`: are packaged as skill/flat
  file as well, so they are available; the router references only the applicable ones.)

### Step B4 — Package protocols by IDE (native skills + flat file fallback)
From the SAME `build_protocol_body(name)`:
1. **Flat file** → `STAGING/.agents/protocols/<name>.md` = body (universal fallback, `<name>` is
   the protocol's source folder name under `templates/protocols/`).
2. **Native skills** per IDE that supports SKILL.md — for each IDE in `IDES` that has
   a native skill path, emit a copy of the frontmatter from
   `$WF_ROOT/templates/protocols/<name>/skill/SKILL.md` (replacing `{{PROTOCOL_BODY: ...}}`
   with the body) in its corresponding directory:

   | IDE | Skills path |
   |-----|-------------|
   | `claude-code` | `STAGING/.claude/skills/<skill-name>/SKILL.md` |
   | `kiro` | `STAGING/.kiro/skills/<skill-name>/SKILL.md` |
   | `codex` | `STAGING/.codex/skills/<skill-name>/SKILL.md` |
   | `windsurf` | `STAGING/.windsurf/skills/<skill-name>/SKILL.md`, `STAGING/.devin/skills/<skill-name>/SKILL.md` (both for Windsurf/Devin compatibility) |
   | `antigravity` | `STAGING/.agents/skills/<skill-name>/SKILL.md` |

   **`<skill-name>` is the skill's `name:` frontmatter field** (read from
   `skill/SKILL.md` before writing), NOT necessarily the protocol's source folder name — e.g.
   the `tdd` protocol packages as skill folder `wf-tdd/`, and `sdd` packages as `wf-sdd-config/`,
   even though their source folders under `templates/protocols/` stay `tdd/`/`sdd/` for internal
   consistency with existing cross-references. This keeps every user/model-facing skill name
   `wf-`-prefixed and unambiguous, without requiring a full source-tree rename.

   If the IDE is not in the table, no native skills are emitted (uses the flat file fallback).
   Register each file in `state.build_plan.protocols_flat` / `.protocols_skills`.
3. **Reference files** — if `$WF_ROOT/templates/protocols/<name>/reference/` exists, copy it
   verbatim (untouched, no `{{PROTOCOL_BODY}}` substitution) alongside every emitted `SKILL.md` for
   that protocol, at `<same-directory-as-SKILL.md>/reference/`. This follows gentle-ai's own
   progressive-disclosure convention (`skills/{skill-name}/references/...`): the file is NOT
   inlined into the skill body, only linked from its `## References` section, so it costs no
   tokens until the model explicitly reads it. Currently applies to `wf-sdd-trigger`.

### Step B5 — Assemble AGENTS.md (thin router)
- Base: `$WF_ROOT/templates/AGENTS.router.md`.
- Replace `{{answers.*}}`, `{{discovery.*}}`, `{{testing.*}}`, `{{mcps.table}}`,
  `{{wizard_version}}` with values from `.wizard-state.json` (deterministic).
  `{{wizard_version}}` is resolved from the root field `wizard_version` of the state.
- Resolve `<if ...>` blocks based on state (testing active, backend, etc.).
- Insert testing sections (`testing-approach.section.md`, `checks.section.md`,
  `data-testid.section.md`) according to `LAYERS`.
- Build the MCPs table based on `STACK` + `LAYERS` (see protocol `architecture`).
- Resolve `{{features.*_yesno}}` to `yes`/`no` based on each boolean feature.
- Footer `wf-version` with `STACK` and `features: ladder={{yes/no}}, tdd={{yes/no}}, routing={{yes/no}}, ci={{yes/no}}, cd={{yes/no}}, release={{yes/no}}` (ALWAYS the last line). Field names in the
  footer are kept as-is for backward compatibility with existing projects/wf-refresh parsing;
  `routing=yes` now means "wf-sdd-trigger is active" (this wizard's own SDD-forcing policy, not
  the retired Route A/B/C model).
- Write to `STAGING/AGENTS.md`.
- **The router NEVER embeds the protocols**; it only has the routing table pointing to them.

### Step B6 — Satellites (per active IDE)
For each IDE ∈ IDES, copy its `$WF_ROOT/templates/satellites/<ide>.tmpl` to the
corresponding destination (see protocol `ides`):
- `claude-code` → `STAGING/CLAUDE.md`
- `vscode-copilot` → `STAGING/.github/copilot-instructions.md`
- `cursor` → `STAGING/.cursor/rules/project.mdc`
- `windsurf` → `STAGING/.windsurf/rules/project.md`
- `kiro` → `STAGING/.kiro/steering/project-context.md`
- `gemini-cli` → `STAGING/GEMINI.md`
- `antigravity` → `STAGING/ANTIGRAVITY.md`
`CLAUDE.md` is ALWAYS generated (Claude does not read AGENTS.md natively).

### Step B7 — Commands (per active IDE)

Commands **always** included (maintenance):
- `/wf-refresh`, `/wf-worktree`, `/wf-settings`, `/wf-onboard`, `/wf-cicd`, `/wf-cleanup`

Commands **conditional** by feature:
- `/wf-ladder`: only if `LADDER == true` (the command to explicitly invoke the wf-ladder steps).

For each command in the catalog (protocol `commands`) and each IDE ∈ IDES:
- body = `$WF_ROOT/templates/commands/<cmd>/_base.md`.
- apply the IDE's frontmatter/path/extension according to the table in protocol `ides`
  (using the `description` from `$WF_ROOT/templates/commands/meta.md` when the IDE requires it).
- write to the IDE's directory (`.claude/commands/`, `.cursor/commands/`,
  `.windsurf/workflows/`, `.kiro/steering/`, `.opencode/commands/`, `.github/prompts/`,
  `.codex/commands/`).
- Exception: Antigravity does not use a separate commands directory. Its slash commands
  are SKILL.md in `.agents/skills/<cmd>/SKILL.md` with `name:` + `description:` frontmatter.
  The body is wrapped in YAML frontmatter just like protocol skills.

### Step B8 — Hook + testing configs

- Hook (dual location — see protocol `cicd`): if the project ALREADY has Husky configured
  (`.husky/` exists), write the hook as `STAGING/.husky/post-commit` using the wrapper
  `$WF_ROOT/templates/protocols/cicd/husky-post-commit.tmpl.md` (which injects the body of
  `hook.post-commit.tmpl.md` without shebang). If there is NO Husky, write
  `STAGING/.git/hooks/post-commit` from `hook.post-commit.tmpl.md` (heredoc, `chmod +x`).
  Never leave the hook in both locations (avoids double triggering).
  **⚠️ Metatemplate `husky-post-commit.tmpl.md`**: has placeholder `{{DRIFT_BODY:
  protocols/cicd/hook.post-commit.tmpl.md}}`. Resolve it by injecting the body of
  `hook.post-commit.tmpl.md` WITHOUT the bash fence, WITHOUT the `#!/bin/bash` shebang,
  and WITHOUT the closing fence. Only the bare script.
- If `LAYERS` includes unit/integration: write
  `$WF_ROOT/templates/protocols/testing/vitest.config.tmpl.md` as
  `STAGING/vitest.config.ts` (strip `# prose header` lines if they exist, no code fence).
  Also generate `src/test/setup.ts` from `setup.tmpl.md`.
- If `LAYERS` includes e2e: write
  `$WF_ROOT/templates/protocols/testing/playwright.config.tmpl.md` as
  `STAGING/playwright.config.ts` (strip `# prose header`). Also
  `$WF_ROOT/templates/protocols/testing/e2e-example.tmpl.md` as
  `STAGING/e2e/example.spec.ts` (raw, already clean). Install browsers.
- **`openspec/config.yaml` is NEVER written or overwritten by the builder**, in any backend. It is
  the exclusive artifact of gentle-ai's `/sdd-init` (see protocol `sdd`, BLOCK RULE). If `BACKEND ∈
  {openspec, hybrid}` and testing/strict_tdd values need to be reflected in it, that happens as a
  **targeted, agent-driven edit** in Phase 4.6b (`phase46b.md`) against the file `/sdd-init` already
  created — never here, never from `config.yaml.tmpl.md` as a stamp. `config.yaml.tmpl.md` is a
  **field reference**, not a file to copy.

### Step B8b — CI and CD (Block 6, from `state.ci` and `state.cd`)
Generate CI and CD artifacts to staging according to `state.ci` and `state.cd` (see subagent-builder-heavy.md for
details) using `$WF_ROOT/templates/protocols/cicd/` as the single source.

**If `CICD == true`** (full CI):
- AI reviewer: `.gga` + `variants/gga-review.yml.md` (if gga), or `claude-review.yml.md` /
  `gemini-review.yml.md`, or nothing (copilot/none).
  - **If `gemini`**: also `.pr_agent.toml` from `variants/pr-agent-config.toml.md`
    (required for pr-agent to run on `synchronize` and `reopened`).
    - **Toggle `auto_improve`**: if `AUTO_IMPROVE == false`, replace
      `github_action_config.auto_improve: "true"` with `"false"` in the assembled template.
  - **If `claude`**: toggle `inline_suggestions` — if `INLINE_SUGGESTIONS == false`,
    omit the `claude_args:` block with `--allowedTools` from the assembled template.
- `quality-guard.yml.md` ALWAYS (conditioned on real scripts). **Fill `{{node_version}}`
  with `state.discovery.node_engine` or 22 by default, and `{{npm_major}}` with
  `state.discovery.npm_major`** — this avoids the `npm ci` lockfile out-of-sync failure.
  - **E2E toggle**: if `state.ci.e2e_in_ci == false`, do not include `npm run test:e2e` in
    the quality guard (even if `LAYERS` includes e2e). The e2e script still exists for local use.
- `.gga`: fill `PR_BASE_BRANCH` with `state.discovery.default_branch` (uncommented).
- **GGA local**: if `local` ∈ gga_modes AND conventional_commits → `.husky/pre-commit` with
  `gga run` (not `gga install`, which Husky shadows). If local without Husky → `gga install` in Phase 8.
- **GGA CI**: `gga-review.yml` installs GGA via `git clone` (NOT `curl|bash`).
- security review if applicable; conventional commits (`.commitlintrc.json`, `.husky/commit-msg`
  in Husky v9+ syntax without shebang) + migration of drift hook to `.husky/post-commit`;
  release-please if applicable.

**If `RELEASE == true` AND `CICD == false`** (release-please standalone):
- Only conventional commits: `.commitlintrc.json`, `.husky/commit-msg` (Husky v9+ without shebang).
- Only release-please: `release-please.yml.md`, `release-please-config.json.md`,
  `release-please-manifest.json.md`, + inject `ai-summary-job.<provider>.yml.md` into `release-please.yml` if `state.ci.release_ai_summary == true`.
- No quality guard, no AI review, no security review.

**If all false**: no CI is generated.

**If `CD == true`** (automatic deploy):
- Select template according to `state.cd.vps_runtime`:
  - `pm2` → `deploy-pm2.node.yml.md`
  - `nginx_php_fpm` → `deploy-nginx-phpfpm.laravel.yml.md`
  - `apache_php_fpm` → `deploy-apache-phpfpm.laravel.yml.md`
  - `docker` → `deploy-docker.yml.md`
- Write `STAGING/.github/workflows/deploy.yml` with placeholders replaced.
- Verify secrets (`SERVER_IP`, `SSH_USER`, `SSH_KEY`).

### Step B9 — Register plan and advance
Populate `state.build_plan` with the exact list of files in staging. Mark
`phases.phase6.status = done`, `phase_pointer = phase7`.

## Phase 8 (promotion)
Phase 8 moves `STAGING/*` to their final destinations, updates `.gitignore`
(`.wizard-state.json`, `.wf-status`, satellite exceptions), and commits. No push.
The review (Phase 7) read from `STAGING/`, not from memory.
