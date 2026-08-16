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

> **`WF_ROOT` definition**: `WF_ROOT` is the wizard repository base URL
> (`https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`), the same
> value as `WF_RAW`. Template files are fetched on demand from
> `$WF_ROOT/templates/...`; they are NOT downloaded to disk by `/wf-init` (only
> the `wf-init/` phase files are). Every `$WF_ROOT/templates/<path>` reference
> below means "fetch that raw URL", never a local filesystem path.

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
> - `.yml.md` / `.json.md` in `variants/` → if the file is wrapped in a markdown code fence, extract from inside it; otherwise use the file raw (CI/CD variant files are raw YAML/JSON and do not need fence extraction)
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
- `IDES=$(jq -r '.answers.ides[]?' .wizard-state.json)`
- `TDD_MODE=$(jq -r '.testing.tdd_mode' .wizard-state.json)`
- `LAYERS=$(jq -r '.testing.layers[]?' .wizard-state.json)`
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
  # SPLIT wizard protocols (wf-ladder, wf-tdd, wf-orchestrator, wf-sdd-trigger) are
  # self-contained under templates/commands/<name>/ (command body + skill + flat, single
  # source). Pure flat-only protocols (architecture, cicd, commands, ides, sdd, testing,
  # workflow) stay under templates/protocols/<name>/.
  if name in (wf-ladder, wf-tdd, wf-orchestrator, wf-sdd-trigger):
    base_dir = $WF_ROOT/templates/commands/<name>
  else:
    base_dir = $WF_ROOT/templates/protocols/<name>
  body = content of <base_dir>/_base.md   # without the internal header comment
  # header injection (presence-driven): wf-ladder ships a protocol-header.md; the protocol
  # artifact (flat + skill) swaps the command header for it. Other SPLIT protocols use the
  # whole _base.md for both command and protocol artifacts.
  if exists <base_dir>/protocol-header.md:
    protocol_header = content of <base_dir>/protocol-header.md   # without the internal header comment
    body = protocol_header + "\n\n" + body from the first "## " heading onward
  # insert stack variant if it exists and applies
  if exists <base_dir>/variants/<STACK>.md:
    body = body with the variant marker replaced by that file
  # special case wf-tdd: variant by mode, not by stack
  if name == "wf-tdd":
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
  OR `TDD == true` — it never duplicates their content, it only sequences which of the active
  `wf-` protocols (`wf-ladder`, `wf-sdd-trigger`, `wf-tdd`) apply.
- If `ROUTING`, `LADDER`, and `TDD` are all false: none of the four `wf-` protocols
  (`wf-ladder`, `wf-sdd-trigger`, `wf-tdd`, `wf-orchestrator`) are built.

Protocols to build (conditional by features):
- `wf-orchestrator`, `wf-ladder`, `wf-sdd-trigger`: per the rules above.
- `wf-tdd` (SPLIT — packaged as command + skill `wf-tdd` + flat): if `TDD == true` AND
  `LAYERS` is not empty (variant = `TDD_MODE`).
- `sdd` (flat file only — single source is the `_base.md`): always when `BACKEND != null`.
- `architecture`: always.
- (`testing`, `cicd`, `ides`, `commands`, `workflow`: flat file only — pure protocols never
  package skills or commands; the router references only the applicable ones.)

### Step B4 — Package protocols by IDE (native skills + flat file fallback)
From the SAME `build_protocol_body(name)`:
1. **Flat file** → `STAGING/.agents/protocols/<name>.md` = body (universal fallback, `<name>` is
   the protocol's source folder name — under `templates/protocols/` for pure protocols,
   `templates/commands/` for the 7 wizard commands that ship skills; the `tdd` protocol was renamed
   `wf-tdd`, so its flat is `.agents/protocols/wf-tdd.md`).
2. **Native skills** per IDE that supports SKILL.md — **presence-driven**: only if
   `<base_dir>/skill/SKILL.md` exists (same SPLIT/pure `base_dir` rule as B3 — all pure
   protocols are flat-only now; only the 7 wizard commands ship skills: the 4 SPLIT
   `wf-ladder`, `wf-tdd`, `wf-orchestrator`, `wf-sdd-trigger` plus the 3 maintenance
   `wf-onboard`, `wf-worktree`, `wf-settings`). For each IDE
   in `IDES` that has a native skill path, emit a copy of the frontmatter from
   `<base_dir>/skill/SKILL.md` (replacing `{{PROTOCOL_BODY: ...}}` with the body) in its
   corresponding directory:

   | IDE | Skills path |
   |-----|-------------|
   | `claude-code` | `STAGING/.claude/skills/<skill-name>/SKILL.md` |
   | `cursor` | `STAGING/.cursor/skills/<skill-name>/SKILL.md` |
   | `kiro` | `STAGING/.kiro/skills/<skill-name>/SKILL.md` |
   | `codex` | `STAGING/.codex/skills/<skill-name>/SKILL.md` |
   | `windsurf` | `STAGING/.windsurf/skills/<skill-name>/SKILL.md`, `STAGING/.devin/skills/<skill-name>/SKILL.md` (both for Windsurf/Devin compatibility) |
   | `gemini-cli` | `STAGING/.gemini/skills/<skill-name>/SKILL.md` |

   **Universal — always emitted, regardless of `IDES`** (the 1:1 skill fallback):
   `STAGING/.agents/skills/<skill-name>/SKILL.md` — the standard `.agents/` path read by
   Codex, OpenCode, Gemini (AGY app), and Devin; covers `antigravity` project-side skills.

   **`<skill-name>` is the skill's `name:` frontmatter field** (read from
   `skill/SKILL.md` before writing), NOT necessarily the command folder name — e.g. the
   `wf-tdd` command folder packages as skill folder `wf-tdd/`. Every user/model-facing skill
   name is `wf-`-prefixed and unambiguous.

   **Note on Cursor and Gemini CLI**: both support native project `SKILL.md` paths (`STAGING/.cursor/skills/<skill-name>/SKILL.md` and `STAGING/.gemini/skills/<skill-name>/SKILL.md`, respectively). The Builder emits the native copy for each active IDE plus the universal `.agents/skills/` copy and the flat `.agents/protocols/` fallback.

   If the IDE is not in the table, only the universal `.agents/skills/` copy and the flat file
   fallback are emitted.
   Register each file in `state.build_plan.protocols_flat` / `.protocols_skills`.
3. **Reference files** — if `<base_dir>/reference/` exists, copy it
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

> **Inference-resolved placeholders**: the following five placeholders have NO
> dedicated state field and are intentionally resolved by the Builder's LLM
> inference from the state + manifest (they cannot be captured as flat JSON
> fields):
> - `{{discovery.commands}}` — exact commands with real flags detected from the manifest (e.g. `npm run lint`, `npm run build`).
> - `{{discovery.conventions.code_style}}` — non-obvious conventions from `state.discovery.conventions` (when present) + reverse engineering.
> - `{{discovery.conventions.structure}}` — short tree of main folders and their purpose.
> - `{{testing.checks_before_done}}` — `lint + build` (+ `test` / `test:e2e` per `state.testing.layers`).
> - `{{mcps.table}}` — the MCPs table built from `state.discovery.stack` + `state.testing.layers` (see protocol `architecture`).
> Never leave the raw placeholder unresolved — always emit real content derived
> from the state.
- Resolve `<if ...>` blocks based on state (testing active, backend, etc.).
- Insert testing sections (`testing-approach.section.md`, `checks.section.md`,
  `data-testid.section.md`) according to `LAYERS`.
- Build the MCPs table based on `STACK` + `LAYERS` (see protocol `architecture`).
- Resolve `{{features.*_yesno}}` to `yes`/`no` based on each boolean feature.
- Validate the final `AGENTS.md`: the `wf-version` footer comment must contain the exact
  `.wizard-state.json` `wizard_version` and the `features` list must reflect the actual
  selected booleans (`routing_abc`, `decision_ladder`, `tdd_protocol`, `ci`, `cd`,
  `release_please`). If any `{{...}}` placeholder or `latest` remains in the footer, fail.
- Footer `wf-version` with `STACK` and `features: ladder={{yes/no}}, tdd={{yes/no}}, routing={{yes/no}}, ci={{yes/no}}, cd={{yes/no}}, release={{yes/no}}` (ALWAYS the last line). Field names in the
  footer are kept as-is for backward compatibility with existing projects/wf-refresh parsing;
  `routing=yes` now means "wf-sdd-trigger is active" (this wizard's own SDD-forcing policy, not
  the retired Route A/B/C model).
- Write to `STAGING/AGENTS.md`.
- **The router NEVER embeds the protocols**; it only has the routing table pointing to them.

### Step B6 — Satellites (per active IDE)
For each IDE ∈ IDES, copy the corresponding satellite template from
`$WF_ROOT/templates/satellites/` to the destination (the template file name uses
a short key, not the full IDE key):

| IDE key | Template | Destination |
|---|---|---|
| `claude-code` | `satellites/claude.tmpl` | `STAGING/CLAUDE.md` |
| `vscode-copilot` | `satellites/copilot.tmpl` | `STAGING/.github/copilot-instructions.md` |
| `cursor` | `satellites/cursor.tmpl` | `STAGING/.cursor/rules/project.mdc` |
| `windsurf` | `satellites/windsurf.tmpl` | `STAGING/.windsurf/rules/project.md` |
| `kiro` | `satellites/kiro.tmpl` | `STAGING/.kiro/steering/project-context.md` |
| `gemini-cli` | `satellites/gemini.tmpl` | `STAGING/GEMINI.md` |
| `antigravity` | `satellites/antigravity.tmpl` | `STAGING/ANTIGRAVITY.md` |

For example, for `claude-code` read `$WF_ROOT/templates/satellites/claude.tmpl`,
not `$WF_ROOT/templates/satellites/claude-code.tmpl`.

`CLAUDE.md` (and its `.claude/` satellite directory) is generated ONLY when
`claude-code` ∈ IDES — exactly like every other IDE's satellite. No IDE is
special-cased: if `claude-code` was not selected, neither `CLAUDE.md` nor
`.claude/skills` is produced.

### Step B7 — Commands (per active IDE)

Commands **always** included (maintenance):
- `/wf-worktree`, `/wf-settings`, `/wf-onboard`

> `/wf-init`, `/wf-refresh`, `/wf-cleanup` are **global-only** commands (installed by
> `install.sh`, never emitted into projects). `/wf-cicd` was archived
> (`templates/_archive/wf-cicd/`); its flow lives in the `cicd` protocol.

Commands **conditional** by feature:
- `/wf-ladder`: only if `LADDER == true` (the command to explicitly invoke the wf-ladder steps).
- `/wf-tdd`: only if `TDD == true` AND `LAYERS` is not empty (the command to invoke the TDD ritual).
- `/wf-orchestrator`: only if `ROUTING == true` OR `LADDER == true` OR `TDD == true`.
- `/wf-sdd-trigger`: only if `ROUTING == true`.

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

> **Skill 1:1** — every command in this catalog is also packaged as a skill (step B4): native
> SKILL.md per IDE + universal `.agents/skills/<cmd>/SKILL.md` + flat
> `.agents/protocols/<cmd>.md`. All 7 wizard commands (4 SPLIT + 3 maintenance) ship skills.

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
  - **Coverage extra (fragment injection)**: if `state.testing.coverage_threshold` is a
    number, inject `$WF_ROOT/templates/protocols/testing/coverage-thresholds.tmpl.md` inside
    the `test: { ... }` block of the generated `vitest.config.ts` (before the closing `}`),
    resolving `{{threshold}}` → `state.testing.coverage_threshold`.
- If `LAYERS` includes e2e: write
  `$WF_ROOT/templates/protocols/testing/playwright.config.tmpl.md` as
  `STAGING/playwright.config.ts` (strip `# prose header`). Also
  `$WF_ROOT/templates/protocols/testing/e2e-example.tmpl.md` as
  `STAGING/e2e/example.spec.ts` (raw, already clean). Install browsers.
  - **Visual regression extra (fragment injection)**: if `state.testing.visual_regression ==
    true`, inject `$WF_ROOT/templates/protocols/testing/visual-snapshots.tmpl.md` inside the
    `defineConfig({ ... })` block of the generated `playwright.config.ts` (before the closing
    `})`), no placeholders to resolve.
- **`openspec/config.yaml` is NEVER written or overwritten by the builder**, in any backend. It is
  the exclusive artifact of gentle-ai's `/sdd-init` (see protocol `sdd`, BLOCK RULE). If `BACKEND ∈
  {openspec, hybrid}` and testing/strict_tdd values need to be reflected in it, that happens as a
  **targeted, agent-driven edit** in Phase 8, step 8.1d (`phase8.md`) against the file `/sdd-init`
  already created — never here, never from `config.yaml.tmpl.md` as a stamp. `config.yaml.tmpl.md` is a
  **field reference**, not a file to copy.

### Step B8b — CI and CD (Block 6, from `state.ci` and `state.cd`)
Generate CI and CD artifacts to staging according to `state.ci` and `state.cd` (see subagent-builder-heavy.md for
details) using `$WF_ROOT/templates/protocols/cicd/` as the single source.

**If `CICD == true`** (full CI):
- AI reviewer: `.gga` + `variants/gga-review.yml.md` (if gga), or `variants/claude-review.yml.md` /
  `variants/gemini-review.yml.md`, or nothing (copilot/none).
  - **If `gemini`**: also `.pr_agent.toml` from `variants/pr-agent-config.toml.md`
    (required for pr-agent to run on `synchronize` and `reopened`).
    - **Toggle `auto_improve`**: if `AUTO_IMPROVE == false`, replace
      `github_action_config.auto_improve: "true"` with `"false"` in the assembled template.
  - **If `claude`**: toggle `inline_suggestions` — if `INLINE_SUGGESTIONS == false`,
    omit the `claude_args:` block with `--allowedTools` from the assembled template.
- `variants/quality-guard.yml.md` ALWAYS (conditioned on real scripts). **Fill `{{node_version}}`
  with `state.discovery.node_engine` or 22 by default, and `{{npm_major}}` with
  `state.discovery.npm_major` or the current npm major (`npm --version | cut -d. -f1`,
  defaulting to `8`)** — this avoids the `npm ci` lockfile out-of-sync failure.
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
- Only release-please: `variants/release-please.yml.md`, `variants/release-please-config.json.md`,
  `variants/release-please-manifest.json.md`, + inject `variants/ai-summary-job.<provider>.yml.md` into `release-please.yml` if `state.ci.release_ai_summary == true`.
  - Resolve `{{release_type}}` in `release-please-config.json` from `state.discovery.stack.primary`:
    use `node` when the primary stack contains `node`, otherwise default to `simple`.
- No quality guard, no AI review, no security review.

**If all false**: no CI is generated.

**If `CD == true`** (automatic deploy):
- Select template according to `state.cd.vps_runtime`:
  - `pm2` → `variants/deploy-pm2.node.yml.md`
  - `nginx_php_fpm` → `variants/deploy-nginx-phpfpm.laravel.yml.md`
  - `apache_php_fpm` → `variants/deploy-apache-phpfpm.laravel.yml.md`
  - `docker` → `variants/deploy-docker.yml.md`
- Write `STAGING/.github/workflows/deploy.yml` with placeholders replaced.
  Resolve both `<if ...>` and `{{if ...}}` / `{{/if}}` markers in deploy templates based on state.
- Verify secrets (`SERVER_IP`, `SSH_USER`, `SSH_KEY`).

### Step B9 — Register plan and advance

Populate `state.build_plan` with the exact list of files in staging, including SHA256 hashes for each file. Mark `phases.phase6.status = done`, `phase_pointer = "phase7"` **only if the current pointer is still `phase6`** (this avoids rewinding state when the Builder is reused by `/wf-refresh`).

**Process**:

1. Source helpers and scan `.wizard-staging/` (null-delimited to handle spaces in paths):
   ```bash
   if [ -f "${WF_DIR:-.}/lib/state-helpers.sh" ]; then
     source "${WF_DIR:-.}/lib/state-helpers.sh"
   else
     # Minimal fallback if WF_DIR is not set (not expected in normal use).
     wf_sha256() {
       if command -v sha256sum >/dev/null 2>&1; then
         sha256sum -- "$1" | awk '{print $1}'
       else
         shasum -a 256 -- "$1" | awk '{print $1}'
       fi
     }
   fi
   cd ".wizard-staging" || { echo "ERROR: .wizard-staging missing — Builder stage failed" >&2; exit 1; }
   FILES="[]"
   PATHS="[]"
   while IFS= read -r -d '' file; do
     REL="${file#./}"
     HASH=$(wf_sha256 "$file")
     FILES=$(jq --arg path "$REL" --arg hash "$HASH" \
       '. += [{"path": $path, "hash": $hash, "managed": true}]' <<< "$FILES")
     PATHS=$(jq --arg path "$REL" \
       '. += [$path]' <<< "$PATHS")
   done < <(find . -type f -print0)
   cd ..
   ```

2. Preserve custom AGENTS.md sections:
   - If `AGENTS.md` exists in project root:
     - Extract all sections inside `<!-- WF: DO NOT REGENERATE -->` markers
     - After Builder generates `.wizard-staging/AGENTS.md`:
       - Re-inject custom sections at same relative location
   - If no existing `AGENTS.md`: use generated version as-is

3. Update state (advance phase only during `wf-init`):
   ```bash
   CURRENT_PHASE=$(jq -r '.phase_pointer // empty' "$WF_STATE")
   # phase5 advances to phase6a-agents (the real key); phase6 is a backward-compatible alias.
   if [ "$CURRENT_PHASE" = "phase6" ] || [ "$CURRENT_PHASE" = "phase6a-agents" ]; then
     jq --argjson files "$FILES" --argjson paths "$PATHS" \
       '.build_plan.generated_files = $files |
        .build_plan.managed_paths = $paths |
        .phases["phase6"].status = "done" |
        .phases["phase6a-agents"].status = "done" |
        .phase_pointer = "phase6b-build-heavy" |
       .updated_at = (now | todate)' "$WF_STATE" > "$WF_STATE.tmp"
   elif [ "$CURRENT_PHASE" = "phase6b-build-heavy" ]; then
     jq --argjson files "$FILES" --argjson paths "$PATHS" \
       '.build_plan.generated_files = $files |
        .build_plan.managed_paths = $paths |
        .phases["phase6"].status = "done" |
        .phases["phase6a-agents"].status = "done" |
        .phases["phase6b-build-heavy"].status = "done" |
        .phase_pointer = "phase7" |
       .updated_at = (now | todate)' "$WF_STATE" > "$WF_STATE.tmp"
   else
     jq --argjson files "$FILES" --argjson paths "$PATHS" \
       '.build_plan.generated_files = $files |
        .build_plan.managed_paths = $paths |
       .updated_at = (now | todate)' "$WF_STATE" > "$WF_STATE.tmp"
   fi
   mv "$WF_STATE.tmp" "$WF_STATE"
   ```

## Phase 8 (promotion)
Phase 8 moves `STAGING/*` to their final destinations, updates `.gitignore`
(`.wizard-state.json`, `.wf-status`, satellite exceptions), and commits. No push.
The review (Phase 7) read from `STAGING/`, not from memory.
