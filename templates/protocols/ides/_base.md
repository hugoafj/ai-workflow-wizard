# Protocol: IDEs (satellites + routing per IDE)

<!--
  SINGLE SOURCE of the multi-IDE compatibility rules. Consumed by the Builder
  (satellites + commands + protocol packaging) and by wf-refresh (derive active
  IDEs). Source: Builder B3/B5 (satellites + commands + protocol packaging),
  phase2 45-55, phase5 15-21, AI_DEV_WORKFLOW 5.4 / 5.7. Satellite templates in
  templates/satellites/*.tmpl. VERBATIM tables in *.section.md.
-->

## Supported IDEs/CLIs

`claude-code`, `cursor`, `windsurf` (Devin), `kiro`, `opencode`, `vscode-copilot`,
`gemini-cli`, `codex`, `antigravity`. The project's active list is stored in `state.answers.ides`
(phase5). In upgrades, it is derived from existing satellites in the repo.

## Protocol packaging per IDE (maximum fidelity)

Each IDE receives protocols in its **native skills format** when supported.
For IDEs without native skills, the fallback is `.agents/protocols/<n>.md` (flat file)
referenced from the AGENTS.md router.

| IDE | Native skills | Skills path | Flat fallback |
|-----|---------------|-------------|----------------|
| Claude Code | ✅ | `.claude/skills/<n>/SKILL.md` | `.agents/protocols/<n>.md` |
| Kiro | ✅ | `.kiro/skills/<n>/SKILL.md` | `.agents/protocols/<n>.md` |
| Codex | ✅ | `.codex/skills/<n>/SKILL.md` | `.agents/protocols/<n>.md` |
| OpenCode | global `~/.config/opencode/skills/` | — (managed by gentle-ai) | `.agents/protocols/<n>.md` |
| Cursor | ✅ | `.cursor/skills/<n>/SKILL.md` | `.agents/protocols/<n>.md` |
| Windsurf/Devin | ✅ | `.windsurf/skills/<n>/SKILL.md`, `.devin/skills/<n>/SKILL.md` | `.agents/protocols/<n>.md` |
| Copilot | ✅ | `.github/skills/` | `.agents/protocols/<n>.md` |
| Gemini CLI | ✅ | `.gemini/skills/<n>/SKILL.md` | `.agents/protocols/<n>.md` |
| Antigravity CLI | ✅ | `.agents/skills/<n>/SKILL.md` | `.agents/protocols/<n>.md` |

> Native skills (SKILL.md) auto-discover and do not require the router to
> mention them. The flat file in `.agents/protocols/` is always the **universal fallback**
> for any IDE that does not support auto-discovery, or for manual reference.
>
> **Wizard skills 1:1** — the 7 project wizard commands (`wf-*`) emit their SKILL.md in the
> IDE's native skills path above **plus** the universal `.agents/skills/<n>/SKILL.md` (always,
> for every IDE) and the flat `.agents/protocols/<n>.md`. Native copies auto-discover; the
> universal copy is the fallback read by Codex/OpenCode/Gemini (AGY app)/Devin and covers
> Antigravity's project-side command path (see B4). Global commands get the same 1:1 from
> `install.sh` (`~/.agents/skills/` + each detected IDE's skill path).

## Command routes and formats table per IDE (VERBATIM)

See `routing-table.section.md` (VERBATIM). Confirmed gotchas:
- Windsurf: `description:` in frontmatter is **required** (without it, it does not appear in the menu).
- Kiro: `inclusion: manual` turns the file into a slash command (`always` would be
  always-on = satellite, a different concept).

## Base paths table per IDE (command verification)

See `base-paths-table.section.md` (VERBATIM phase2 45-55).

## Satellites

One satellite per active IDE, all pointing to AGENTS.md — including `CLAUDE.md`, which is
generated ONLY when `claude-code` is in `state.answers.ides` (Claude does not natively read
AGENTS.md as of June 2026, but if Claude Code is not an active IDE, no `CLAUDE.md` or `.claude/`
directory is produced). Each satellite template is available at:
`https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/satellites/`.
