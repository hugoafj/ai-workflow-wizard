**Routes and formats table per IDE** (verified against official documentation):

| IDE | Directory | Format |
|---|---|---|
| Claude Code | `.claude/commands/` | Plain markdown, no frontmatter |
| Cursor | `.cursor/commands/` | Plain markdown, no frontmatter |
| Windsurf/Devin | `.windsurf/workflows/` | Frontmatter with `description:` required |
| Kiro | `.kiro/steering/` | Frontmatter with `inclusion: manual` |
| OpenCode | `.opencode/commands/` | Plain markdown, no frontmatter |
| Copilot | `.github/prompts/` | Suffix `.prompt.md` + frontmatter `agent: 'agent'` |
| Codex | `.codex/commands/` | Plain markdown, no frontmatter |
| Antigravity | `.agents/skills/<name>/SKILL.md` | Frontmatter `name:` + `description:` — the SKILL.md itself works as a slash command |

> **Global commands (install.sh)**: `wf-init`, `wf-refresh`, and `wf-cleanup` are installed
> user-level as slash commands in every detected IDE (Windsurf `global_workflows/`, Codex
> `~/.codex/commands/`, Claude `~/.claude/commands/`, Cursor `~/.cursor/commands/`, Kiro
> `~/.kiro/steering/`, Copilot `~/.copilot/`, Antigravity skills, OpenCode
> `~/.config/opencode/commands/`) and, 1:1, as SKILL.md in each IDE's global skills path plus
> `~/.agents/skills/`.

> **Wizard skills 1:1**: every project command in the table above also ships a matching
> SKILL.md (Builder B4) in the active IDE's skills path (`.claude/skills/`, `.kiro/skills/`,
> `.codex/skills/`, `.windsurf/skills/`, `.devin/skills/`) plus the universal
> `.agents/skills/<cmd>/SKILL.md` and the flat `.agents/protocols/<cmd>.md` fallback —
> so the command works as a slash command AND as a natural-language-invocable skill.

> **Implementation note**: before writing commands for Windsurf or Kiro, verify that the target directories exist. For Windsurf, `description:` in frontmatter is required — without it, the workflow does not appear in the slash menu. For Kiro, `inclusion: manual` is what turns the file into a slash command — with `inclusion: always` it would be an always-on context rule (a different concept, already covered by satellites).
