<!--
  This is the AGENTS.md template that the Builder (wf-init/lib/builder.md) writes to
  the target project. It is a THIN ROUTER (constraint 7): only global policies,
  project-specific content and routing to packaged protocols. It NEVER contains
  the full protocols (Decision Ladder, Local Orchestration, TDD) — those live in
  .claude/skills/<n>/ and .agents/protocols/<n>.md, and the router points to them.

  The {{PLACEHOLDERS}} are filled deterministically from .wizard-state.json.
  The <if ...> blocks are conditionals that the Builder resolves by state (not by
  model judgment).
-->

# AGENTS.md — {{answers.project_name}} — {{answers.stack_versions}}

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
| Windsurf | `~/.codeium/windsurf/skills/` | `.windsurf/skills/` |
| Codex CLI | `~/.codex/skills/` | `.codex/skills/` |
| Copilot | `~/.copilot/skills/` | `.github/skills/` |
| Kiro | `~/.kiro/skills/`, `~/.kiro/steering/` | `.kiro/skills/`, `.kiro/steering/` |
| Gemini CLI | `~/.gemini/skills/` | `.gemini/skills/`, `.agents/skills/` |
| Antigravity | `~/.gemini/antigravity/skills/`, `~/.gemini/antigravity-ide/skills/`, `~/.gemini/antigravity-cli/skills/` | `.agents/skills/` |

### Available protocols

| When | Protocol to read |
<if state.features.routing_abc or state.features.decision_ladder>
| Before classifying or implementing any task | `decision-ladder` — Decision Ladder<if state.features.routing_abc> + Local Orchestration (Routes A/B/C, Preflight, Route B Lock, Precheck)</if> |
</if>
<if state.features.tdd_protocol>
| Before writing tests or code for a feature | `tdd` — TDD Protocol |
</if>
<if state.sdd.backend != null>
| On Route B or C — SDD pipeline | SDD skills live in your IDE's path (see table above). **READ them before delegating** — do not invent the flow. Available skills: `sdd-propose`, `sdd-spec`, `sdd-design`, `sdd-tasks`, `sdd-apply`, `sdd-verify`, `sdd-archive`, `sdd-explore`, `sdd-init`, `sdd-onboard` |
| When initializing SDD or migrating backend | `sdd` — SDD Protocol |
</if>
| When generating/auditing AGENTS.md | `architecture` — AI context architecture |

> **⚠️ MANDATORY RULE**: Before implementing any change, look for the
> corresponding skill in your IDE's path and READ it. Do NOT invent SDD flows
> or assume you know how it works — the skills contain the exact
> procedure.

<if state.features.routing_abc>
> **Universal order**: 🪜 Decision Ladder → 🔍 Preflight → (by route) 🧪 TDD → implementation.
>
> **✅ Single gate — paste the PRECHECK before production code**: just before touching
> any production file (or starting SDD on Route C), paste the **`✅ PRECHECK
> PRE-IMPLEMENTATION`** block from the `decision-ladder` protocol (Section 5) with each item resolved. If
> any applicable item is ✗ or not done, STOP. It is an EXTERNAL gate: if you did not paste it,
> you did not start. Summary of its items (details in the `decision-ladder` protocol):
> - **Preflight**: mandatory on all routes (including A), with visible Route + Impact Analysis. The decision tree is calculated silently (do not paste it as Q1/Q2/Q3). The Ladder does not replace it.
> - **Route B**: the SDD Lite Checklist is an external gate (one ✗ → Route C); show the locking menu and STOP to wait for the user's choice before code. The `/sdd-lite` command delegates each phase to the corresponding sub-agent using the IDE's native delegation mechanism (`task()`, `spawn_agent()`, `run_subagent()`, etc.).
> - **Route C**: you declare the mandatory start of the SDD pipeline and delegate to gentle-ai's SDD skills; no inline proposal, no direct implementation, no TDD Proposal at pipeline level. Delegate using the IDE's native delegation mechanism (`task()`, `spawn_agent()`, `run_subagent()`, etc.).
<if state.features.tdd_protocol>
> - **TDD**: never production code without the mode's TDD ritual (🧪 TDD PROPOSAL in standard / RED→GREEN evidence in strict). On Route A it goes before implementing. **On B/C the `🧪 TDD PROPOSAL` (standard mode) is issued by the ORCHESTRATOR before delegating to `sdd-apply` — which is headless and cannot ask — and only then delegates with the *baked* decision + injected `tdd-protocol` (see row above).** Real bug fixed: Route C was doing it and TDD ran; Route B/SDD Lite delegated without emitting the proposal.
</if>
</if>
</if>
<if not state.features.routing_abc and not state.features.decision_ladder and not state.features.tdd_protocol>
<!-- No agent protocols: the project does not use Ladder, Routes ABC or TDD. -->
</if>

<!-- The following HTML comment is mandatory and must remain as the LAST LINE of the
     file, as-is, with real values (read by /wf-settings and /wf-refresh by reading
     the full line `features:.*`; if missing, both commands treat all features
     as unknown). -->
<!-- wf-version: {{wizard_version}} | source: github.com/hugoafj/ai-workflow-wizard | stack: {{discovery.stack_key}} | features: ladder={{features.decision_ladder_yesno}}, tdd={{features.tdd_protocol_yesno}}, routing={{features.routing_abc_yesno}}, ci={{features.ci_yesno}}, cd={{features.cd_yesno}}, release={{features.release_please_yesno}} -->
