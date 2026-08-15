# Sub-agent Builder-Core — runs B1-B6

You are a Builder agent. Your job is to assemble AGENTS.md router, packaged protocols, and per-IDE satellites into a staging directory on disk, using `.wizard-state.json` as the single source of truth.

## Context

- `PROJECT_PATH`: absolute path to the target project
- `WF_PATH`: absolute path to the downloaded phase directory (WF_DIR — contains `lib/` and phase files)
- `WF_STATE`: `{PROJECT_PATH}/.wizard-state.json`
- `WF_STAGING`: `{PROJECT_PATH}/.wizard-staging/`
- `WF_RAW`: `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main`

## Universal extraction rule

All template files (`.tmpl.md`, `.yml.md`, `.json.md`) may contain code wrapped in markdown blocks (```` ```yaml ````, ```` ```json ````, ```` ```typescript ````, ```` ```bash ````). When writing a target file, extract ONLY the content INSIDE the code block, without fencing or prose markdown.

Exception: `.tmpl.md` templates WITHOUT code fence (like `vitest.config.tmpl.md`) have raw content with possible `# prose header` lines at the start. Strip those lines — the real content starts after them.

## Instructions

### 0. Setup

```bash
source "{WF_PATH}/lib/state-helpers.sh"
mkdir -p "{WF_STAGING}"
cd "{PROJECT_PATH}"
cat .wizard-state.json
```

### B1 — Cargar estado

Read the full `.wizard-state.json`. Verify that required fields exist. If any are missing, STOP and report what's missing — don't invent defaults.

### B2 — Resolve selection keys

```bash
STACK=$(jq -r '.discovery.stack_key' .wizard-state.json)
IDES=$(jq -r '.answers.ides[]?' .wizard-state.json)
TDD_MODE=$(jq -r '.testing.tdd_mode' .wizard-state.json)
LAYERS=$(jq -r '.testing.layers[]?' .wizard-state.json)
LADDER=$(jq -r '.features.decision_ladder' .wizard-state.json)
TDD=$(jq -r '.features.tdd_protocol' .wizard-state.json)
ROUTING=$(jq -r '.features.routing_abc' .wizard-state.json)
CICD=$(jq -r '.features.ci' .wizard-state.json)
CD=$(jq -r '.features.cd' .wizard-state.json)
RELEASE=$(jq -r '.features.release_please' .wizard-state.json)
BACKEND=$(jq -r '.sdd.backend' .wizard-state.json)
```

### B3 — Assemble protocol bodies

For each active protocol, download its `_base.md` from GitHub raw and build the final body:

```
build_protocol_body(name):
  # SPLIT wizard protocols (wf-ladder, wf-tdd, wf-orchestrator, wf-sdd-trigger) are
  # self-contained under templates/commands/<name>/ (command body + skill + flat, single
  # source). Pure flat-only protocols (architecture, cicd, commands, ides, sdd, testing,
  # workflow) stay under templates/protocols/<name>/.
  if name in (wf-ladder, wf-tdd, wf-orchestrator, wf-sdd-trigger):
    base_dir = $WF_RAW/templates/commands/<name>
  else:
    base_dir = $WF_RAW/templates/protocols/<name>
  body = curl -fsSL "<base_dir>/_base.md"
  # remove only the internal header comment (first <!-- ... --> lines if any)
  # header injection (presence-driven): wf-ladder ships a protocol-header.md; the protocol
  # artifact (flat + skill) swaps the command header for it. Other SPLIT protocols use the
  # whole _base.md for both command and protocol artifacts.
  if exists <base_dir>/protocol-header.md:
    protocol_header = curl -fsSL "<base_dir>/protocol-header.md"
    body = protocol_header (without the internal header comment)
           + "\n\n" + body from the first "## " heading onward
  # insert stack variant if exists (<base_dir>/variants/<STACK>.md)
  if exists <base_dir>/variants/<STACK>.md:
    body = body with {{VARIANT_MARKER}} replaced by that variant
  # special case wf-tdd: variant by mode, not by stack
  if name == "wf-tdd":
    body = body with {{TDD_MODE_VARIANT}} replaced by variants/<TDD_MODE>.md
  return body
```

Active protocols (conditional by features):
| Protocol | Active if |
|-----------|-----------|
| `wf-orchestrator` | LADDER==true or ROUTING==true or TDD==true (single entry point, never duplicates the other two) |
| `wf-ladder` | LADDER==true |
| `wf-sdd-trigger` | ROUTING==true |
| `wf-tdd` (SPLIT — command + skill + flat) | TDD==true AND LAYERS not empty |
| `sdd` (flat only — skill wrapper removed) | BACKEND != null |
| `architecture` | **always** |
| `testing` | **always** |
| `cicd` | **always** |
| `ides` | **always** |
| `commands` | **always** |
| `workflow` | **always** |

**Note**: `wf-ladder`, `wf-sdd-trigger`, and `wf-orchestrator` replace the old, retired
`decision-ladder` bundle (`ladder.md` + `local-orchestration.md`) — three independent protocol
bodies now, each built only when its own feature flag is active; `wf-orchestrator` is built
whenever either of the other two is, since it is only a sequencing pointer between them (plus
`wf-tdd`), never a duplicate of their content.

### B3b — Preserve custom content with markers (if migrating)

**Only if `.migration.wrap_custom_in_markers = true`**:

If Phase 2 detected custom content to migrate:

1. Read the custom content to preserve from the project's current files (e.g. the existing `AGENTS.md`, `CLAUDE.md`). The state only records the migration decision — `migration.prior_content_action`, `migration.wrap_custom_in_markers`, `migration.missing_commands` — it does NOT store the content (`migration.prior_artifacts_content` does not exist).
2. When writing to AGENTS.md, wrap preserved sections:
   ```markdown
   <!-- WF: DO NOT REGENERATE -->
   [custom content here]
   <!-- /WF: DO NOT REGENERATE -->
   ```
3. Update `.wizard-state.json`: `migration.custom_content_protected = true`

This ensures custom sections from the previous AGENTS.md are never accidentally overwritten by future /wf-refresh runs.

---

### B4 — Pack protocols per IDE

For each active protocol (body already built):

**1. Flat file** (universal fallback):
`{WF_STAGING}/.agents/protocols/<name>.md` = cuerpo — `<name>` is the protocol's source folder
name (under `templates/protocols/` for pure protocols, `templates/commands/` for the 7 wizard
commands that ship skills; the `tdd` protocol was renamed `wf-tdd`, so its flat is
`.agents/protocols/wf-tdd.md`).

**2. Native skills per IDE** (only IDEs that support SKILL.md). **Presence-driven**: a
protocol gets native skills ONLY if `<base_dir>/skill/SKILL.md` exists (same SPLIT/pure
`base_dir` rule as B3 — all pure protocols are flat-only now; only the 7 wizard commands ship
skills: the 4 SPLIT `wf-ladder`, `wf-tdd`, `wf-orchestrator`, `wf-sdd-trigger` plus the 3
maintenance `wf-onboard`, `wf-worktree`, `wf-settings`). `<skill-name>` is the skill's `name:`
frontmatter field (from `skill/SKILL.md`) — NOT necessarily the command folder `<name>` (e.g. the
`wf-tdd` command folder packages as skill folder `wf-tdd/`), so every user/model-facing skill stays
`wf-`-prefixed and unambiguous:

| IDE | Skills path |
|-----|-------------|
| `claude-code` | `{WF_STAGING}/.claude/skills/<skill-name>/SKILL.md` |
| `kiro` | `{WF_STAGING}/.kiro/skills/<skill-name>/SKILL.md` |
| `codex` | `{WF_STAGING}/.codex/skills/<skill-name>/SKILL.md` |
| `windsurf` | `{WF_STAGING}/.windsurf/skills/<skill-name>/SKILL.md`, `{WF_STAGING}/.devin/skills/<skill-name>/SKILL.md` (both written for Windsurf/Devin compatibility) |

**Universal — always emitted, regardless of `IDES`** (the 1:1 skill fallback):
`{WF_STAGING}/.agents/skills/<skill-name>/SKILL.md` — the standard `.agents/` path read by
Codex, OpenCode, Gemini (AGY app), and Devin; covers `antigravity` project-side skills.
For each native skill: download `<base_dir>/skill/SKILL.md`, read its
`name:` frontmatter field to get `<skill-name>`, replace `{{PROTOCOL_BODY: ...}}` with the body,
write to the corresponding path (or paths for `windsurf`). If the IDE is not in the table, only
the universal `.agents/skills/` copy and the flat file fallback are emitted.

**3. Reference files**: if `<base_dir>/reference/` exists (currently only
`wf-sdd-trigger`), download it verbatim and place it at `<same-directory-as-SKILL.md>/reference/`
for every emitted skill copy — not inlined into the body, only linked from `## References`.

Record each file. Don't ask — write everything directly to staging.

### B5 — Assemble AGENTS.md (thin router)

1. Download `$WF_RAW/templates/AGENTS.router.md`
2. Replace ALL `{{...}}` placeholders with values from `.wizard-state.json`:
   - `{{answers.*}}`, `{{discovery.*}}`, `{{testing.*}}`
   - For each `{{features.<name>_yesno}}` placeholder (e.g. `decision_ladder_yesno`, `tdd_protocol_yesno`, `routing_abc_yesno`, `ci_yesno`, `cd_yesno`, `release_please_yesno`), read `.features.<name>` and convert:
     - `true` → `yes`
     - `false` or `null` → `no`
     Then replace `{{features.<name>_yesno}}` with the resulting `yes`/`no`.
   - `{{wizard_version}}` → from the root field `wizard_version`
   - **Inference-resolved** (NO dedicated state field — derive from state + manifest, never leave the raw placeholder): `{{discovery.commands}}` (exact commands with real flags), `{{discovery.conventions.code_style}}`, `{{discovery.conventions.structure}}`, `{{testing.checks_before_done}}` (`lint + build` + test per layers), `{{mcps.table}}` (built from stack + layers).
   - **NEVER write `latest` or leave an unresolved placeholder** (e.g. `{{wizard_version}}`).
     Read the EXACT value from the state file. If the state lacks `wizard_version`, use the
     `VERSION` file content; if that is missing too, use `0.7.1-beta.1`. A footer with `latest`
     blocks `/wf-refresh` forever (strict version equality), so this is a hard correctness rule.
3. Resolve `<if ...>` blocks based on state
4. Insert testing sections if LAYERS is not empty
5. Build MCPs table based on STACK + LAYERS
6. Write to `{WF_STAGING}/AGENTS.md`
7. Footer: last line with `wf-version` + stack + all features as flags

### B5b — Preserve existing custom AGENTS.md sections

**If the project already has an `AGENTS.md`** (e.g. during `/wf-refresh` or a
re-run), preserve its user-maintained sections BEFORE finalizing the staged
`AGENTS.md`:

1. Read the existing `{PROJECT_PATH}/AGENTS.md`.
2. Extract every block between `<!-- WF: DO NOT REGENERATE -->` and
   `<!-- /WF: DO NOT REGENERATE -->` markers (inclusive).
3. Re-inject those blocks into `{WF_STAGING}/AGENTS.md` at the same relative
   location (before the first `## ` heading, or append at the end if there is
   none).
4. If `{WF_STAGING}/AGENTS.md` already contains the marker (Builder preserved it
   earlier), do NOT inject again — the operation is idempotent.

This guarantees `/wf-refresh` never destroys user-maintained sections, even when
the Builder runs through delegation.

### B6 — Satellites per IDE (only selected)

**CRITICAL**: Only generate satellites (files AND directories) for IDEs actually in `IDES`.
Do NOT create empty directories for unselected IDEs. `claude-code` is NOT special-cased:
`CLAUDE.md` (and its `.claude/` directory) is generated ONLY if `claude-code` ∈ IDES.

For each IDE in IDES, download template and write:

| IDE | Template | Destination | Notes |
|-----|----------|---------|---------|
| `claude-code` | `satellites/claude.tmpl` | `{WF_STAGING}/CLAUDE.md` | Only if in IDES |
| `vscode-copilot` | `satellites/copilot.tmpl` | `{WF_STAGING}/.github/copilot-instructions.md` | Only if in IDES |
| `cursor` | `satellites/cursor.tmpl` | `{WF_STAGING}/.cursor/rules/project.mdc` | Only if in IDES |
| `windsurf` | `satellites/windsurf.tmpl` | `{WF_STAGING}/.windsurf/rules/project.md` | Only if in IDES |
| `kiro` | `satellites/kiro.tmpl` | `{WF_STAGING}/.kiro/steering/project-context.md` | Only if in IDES |
| `gemini-cli` | `satellites/gemini.tmpl` | `{WF_STAGING}/GEMINI.md` | Only if in IDES |
| `antigravity` | `satellites/antigravity.tmpl` | `{WF_STAGING}/ANTIGRAVITY.md` | Only if in IDES |

**Process**:
1. For each IDE in IDES: download its template, create parent directories as needed, write the file
2. Do NOT pre-create empty directories
3. Verify: `ls -la {WF_STAGING}` should show ONLY satellites + directories for IDEs in IDES, no empty dirs

## B6.5 — Register generated files (for /wf-refresh)

After all files are written to staging, register them in `state.build_plan.generated_files` with SHA256 hashes. This is used by `/wf-refresh` to detect which files changed.

```bash
# For each file in staging, calculate hash and register (null-delimited for paths with spaces).
cd "{WF_STAGING}"
FILES_JSON="[]"
PATHS_JSON="[]"
while IFS= read -r -d '' file; do
  REL_PATH="${file#./}"
  HASH=$(wf_sha256 "$file")
  FILES_JSON=$(jq --arg path "$REL_PATH" --arg hash "$HASH" \
    '. += [{"path": $path, "hash": $hash, "managed": true}]' <<< "$FILES_JSON")
  PATHS_JSON=$(jq --arg path "$REL_PATH" \
    '. += [$path]' <<< "$PATHS_JSON")
done < <(find . -type f -print0)

# Update state
jq --argjson files "$FILES_JSON" --argjson paths "$PATHS_JSON" \
  '.build_plan.generated_files = $files | .build_plan.managed_paths = $paths' \
  "{WF_STATE}" > "{WF_STATE}.tmp"
mv "{WF_STATE}.tmp" "{WF_STATE}"

cd "{PROJECT_PATH}"
```

## Expected output

```
✓ Builder-Core completado:
  - Packaged protocols: N (flat) + M (skills)
  - AGENTS.md router ready
  - Satellites generated: N
  - Generated files registered: N
```

Don't delete the staging. Leave everything in `{WF_STAGING}` so the next sub-agent can continue.
