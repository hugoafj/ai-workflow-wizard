Apply the same pattern to each active IDE, adjusting path and extension.

### Commands per IDE

| IDE | Base path | Extension |
|---|---|---|
| Claude Code | `.claude/commands/` | `.md` |
| Cursor | `.cursor/commands/` | `.md` |
| Windsurf | `.windsurf/workflows/` | `.md` |
| Kiro | `.kiro/steering/` | `.md` (caution: mixes satellites `inclusion: always` with commands `inclusion: manual` — verify by name, don't assume) |
| OpenCode | `.opencode/commands/` | `.md` |
| Copilot | `.github/prompts/` | `.prompt.md` |

### Skills per IDE/CLI (SKILL.md)

| IDE/CLI | Global path | Project path | Notes |
|---|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` | native auto-discovery |
| OpenCode | `~/.config/opencode/skills/` | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` | also reads compatible paths |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` | compatible with `~/.codex/skills` and `~/.claude/skills` |
| Windsurf/Devin | `~/.codeium/windsurf/skills/`, `~/.config/devin/skills/` | `.windsurf/skills/`, `.devin/skills/` | gentle-ai sync; Devin uses XDG path |
| Codex CLI | `~/.codex/skills/` | `.codex/skills/` | also recognizes `~/.agents/skills/` |
| Copilot | `~/.copilot/skills/` | `.github/skills/` | — |
| Kiro | `~/.kiro/skills/`, `~/.kiro/steering/` | `.kiro/skills/`, `.kiro/steering/` | native auto-discovery |
| Gemini CLI | `~/.gemini/skills/` | `.gemini/skills/`, `.agents/skills/` | alias `.agents/skills/` |
| Antigravity | `~/.gemini/antigravity/skills/`, `~/.gemini/antigravity-ide/skills/`, `~/.gemini/antigravity-cli/skills/` | `.agents/skills/` | see note below |

> **Antigravity note**: Google is migrating toward a scheme where `config/` is the
> shared source. The active paths are: `antigravity/skills/`, `antigravity-cli/skills/`,
> `antigravity-ide/skills/`, `config/skills/`. Use all 4 until the canonical one is confirmed.
