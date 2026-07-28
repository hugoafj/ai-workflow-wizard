**Routes and formats table per IDE** (verified against official documentation):

| IDE | Directory | Format |
|---|---|---|
| Claude Code | `.claude/commands/` | Plain markdown, no frontmatter |
| Cursor | `.cursor/commands/` | Plain markdown, no frontmatter |
| Windsurf/Devin | `.windsurf/workflows/` | Frontmatter with `description:` required |
| Kiro | `.kiro/steering/` | Frontmatter with `inclusion: manual` |
| OpenCode | `.opencode/commands/` | Plain markdown, no frontmatter |
| Copilot | `.github/prompts/` | Suffix `.prompt.md` + frontmatter `mode: agent` |
| Codex | `.codex/commands/` | Plain markdown, no frontmatter |
| Antigravity | `.agents/skills/<name>/SKILL.md` | Frontmatter `name:` + `description:` — the SKILL.md itself works as a slash command |

> **Implementation note**: before writing commands for Windsurf or Kiro, verify that the target directories exist. For Windsurf, `description:` in frontmatter is required — without it, the workflow does not appear in the slash menu. For Kiro, `inclusion: manual` is what turns the file into a slash command — with `inclusion: always` it would be an always-on context rule (a different concept, already covered by satellites).
