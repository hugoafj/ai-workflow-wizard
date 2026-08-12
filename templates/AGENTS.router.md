<!--
  This is the AGENTS.md template that the Builder (wf-init/lib/builder.md) writes to
  the target project. It is a THIN ROUTER (constraint 7): only global policies,
  project-specific content and routing to packaged protocols. It NEVER contains
  the full protocols (wf-orchestrator, wf-ladder, wf-sdd-trigger, wf-tdd) — those live in
  .claude/skills/<n>/ and .agents/protocols/<n>.md, and the router points to them.

  The {{PLACEHOLDERS}} are filled deterministically from .wizard-state.json.
  The <if ...> blocks are conditionals that the Builder resolves by state (not by
  model judgment).
-->

# AGENTS.md — {{answers.project_name}} — {{answers.stack_versions}}

<if state.features.routing_abc or state.features.decision_ladder or state.features.tdd_protocol>
> **⛔ HARD STOP RULE — always follow wf-orchestrator skill first.**
>
> always follow wf-orchestrator.md skill first. Before classifying, planning, or implementing
> any task, READ `wf-orchestrator` (the project's packaged skill — see Protocol routing below).
> It is the single entry point and source of truth for this project's workflow: it decides the
> gate sequence (Ladder → Preflight → Decision → TDD ritual). If you skipped it, STOP and read
> it before doing anything else.
</if>

## Commands

{{discovery.commands}}  <!-- exact commands with real flags detected from manifest -->

## Code Style & Conventions

{{discovery.conventions.code_style}}  <!-- only non-obvious things, from reverse engineering + answers -->

## Project Structure

{{discovery.conventions.structure}}  <!-- short tree, main folders and their purpose -->

## Critical Constraints

{{answers.critical_constraints}}  <!-- what the agent must NOT do + sensitive versions -->

<if state.testing.layers not empty>
## Testing Approach

<!-- Insert testing-approach.section.md from the testing protocol, adapted to the stack -->
{{protocols/testing/testing-approach.section.md}}
</if>

## Programmatic Checks

{{testing.checks_before_done}}  <!-- lint + build (+ test/test:e2e per state.testing) -->

## Project MCPs

<!--
  This section is read by /wf-onboard to know which MCPs to configure on each machine.
  It is built according to state.discovery.stack and state.testing (see architecture protocol).
-->
{{mcps.table}}

## Behavior Preferences

<!-- VERBATIM from the architecture protocol (Behavior Preferences). Always written. -->
- Review gate before commit: show me the full diff and wait for my approval before committing.
- No opportunistic refactor: stick to the new pattern only in new code.
- If you detect that the code contradicts something in this AGENTS.md, report it at the end of
  your reply with the tag `[AGENTS.md drift detected: <description>]`. Do not correct AGENTS.md yourself.

---

<if state.features.routing_abc or state.features.decision_ladder or state.features.tdd_protocol>
## 🧭 Protocol routing (load on demand)

This project uses packaged protocols that are loaded **only when applicable**, to avoid
bloating the context. They are NOT written in full here — they live in dedicated files.

### Skill paths by IDE/CLI

| IDE/CLI | Global skill path | Project path |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| OpenCode | `~/.config/opencode/skills/` | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |
| Windsurf/Devin | `~/.codeium/windsurf/skills/`, `~/.config/devin/skills/` | `.windsurf/skills/`, `.devin/skills/` |
| Codex CLI | `~/.codex/skills/` | `.codex/skills/` |
| Copilot | `~/.copilot/skills/` | `.github/skills/` |
| Kiro | `~/.kiro/skills/`, `~/.kiro/steering/` | `.kiro/skills/`, `.kiro/steering/` |
| Gemini CLI | `~/.gemini/skills/` | `.gemini/skills/`, `.agents/skills/` |
| Antigravity | `~/.gemini/antigravity/skills/`, `~/.gemini/antigravity-ide/skills/`, `~/.gemini/antigravity-cli/skills/`, `~/.gemini/config/skills/` (canonical) | `.agents/skills/` |

### Available protocols

> **Namespace note**: everything prefixed `wf-` below is owned by THIS wizard, never by
> gentle-ai. Anything named `sdd-*` (no `wf-` prefix) is gentle-ai's own — its routing and
> delegation mechanics are gentle-ai's exclusive authority, already installed/synced for your
> IDE. This wizard's own protocols never re-specify HOW gentle-ai delegates or routes.

| When | Protocol to read |
<if state.features.routing_abc or state.features.decision_ladder or state.features.tdd_protocol>
| Before classifying or implementing any task | `wf-orchestrator` — single entry point to this project's own wf- protocols<if state.features.decision_ladder> (loads `wf-ladder`)</if><if state.features.routing_abc> (loads `wf-sdd-trigger`)</if><if state.features.tdd_protocol> (loads `wf-tdd`)</if> |
</if>
<if state.features.tdd_protocol>
| Before writing tests or code for a feature | `wf-tdd` — TDD Protocol (wizard-owned) |
</if>
<if state.sdd.backend != null>
| When gentle-ai's SDD was explicitly requested (via `wf-sdd-trigger`'s `wf-force-sdd` outcome) | SDD skills live in your IDE's path (see table above) — **gentle-ai's own**, not this wizard's. **READ them before relying on them** — do not invent the flow, and do not describe how they delegate; that is gentle-ai's own native content for this adapter. Available skills: `sdd-propose`, `sdd-spec`, `sdd-design`, `sdd-tasks`, `sdd-apply`, `sdd-verify`, `sdd-archive`, `sdd-explore`, `sdd-init`, `sdd-onboard` |
| When migrating SDD backend or touching `openspec/config.yaml`'s known fields | `sdd` — wizard-owned rules (persistence backends, Wizard-Allowed Field Edits) — flat file `.agents/protocols/sdd.md` |
</if>
| When generating/auditing AGENTS.md | `architecture` — AI context architecture |

> **⚠️ MANDATORY RULE**: Before implementing any change, look for the
> corresponding skill in your IDE's path and READ it. Do NOT invent SDD flows
> or assume you know how it works — the skills contain the exact
> procedure.

<if state.features.routing_abc>
> **Universal order**: 🪜 `wf-ladder` (if active) → 🔍 `wf-preflight` (user confirms) → (by outcome) 🧪 `wf-tdd` → implementation.
>
> **No combined PRECHECK**: after the user confirms the `wf-preflight`, proceed directly to the chosen route. Summary of the outcome (details in the `wf-sdd-trigger` protocol):
> - **`wf-no-sdd`**: implement directly (or with 🧪 `wf-tdd` if active). No SDD request needed.
> - **`wf-force-sdd`**: declare the explicit SDD request to gentle-ai via `sdd-new <feature or fix>` (or `/sdd-new` if your adapter only supports native slash syntax). How gentle-ai delegates/executes is entirely its own decision per adapter — never re-specified by this wizard.
<if state.features.tdd_protocol>
> - **`wf-tdd`**: never production code without the mode's TDD ritual (🧪 TDD PROPOSAL in standard / RED→GREEN evidence in strict). On `wf-no-sdd` it goes before implementing. **When `wf-force-sdd` was requested, the `🧪 TDD PROPOSAL` (standard mode) is issued by you (the orchestrator) BEFORE making the `sdd-apply` request — since `sdd-apply` is headless and cannot ask — and only then is the request made with the *baked* decision + a reference to `wf-tdd` (see row above).**
</if>
</if>
</if>
<if not state.features.routing_abc and not state.features.decision_ladder and not state.features.tdd_protocol>
<!-- No agent protocols: the project does not use wf-ladder, wf-sdd-trigger, or wf-tdd. -->
</if>

<!-- The following HTML comment is mandatory and must remain as the LAST LINE of the
     file, as-is, with real values (read by /wf-settings and /wf-refresh by reading
     the full line `features:.*`; if missing, both commands treat all features
     as unknown). -->
<!-- wf-version: {{wizard_version}} | source: github.com/hugoafj/ai-workflow-wizard | stack: {{discovery.stack_key}} | features: ladder={{features.decision_ladder_yesno}}, tdd={{features.tdd_protocol_yesno}}, routing={{features.routing_abc_yesno}}, ci={{features.ci_yesno}}, cd={{features.cd_yesno}}, release={{features.release_please_yesno}} -->
