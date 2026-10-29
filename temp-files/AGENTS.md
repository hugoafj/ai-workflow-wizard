# Gentle AI — Legacy Path Bridge for Windsurf/Devin

> **⛔ HARD MANDATORY RULE — read this entire section before any action.**
>
> This section is a **binding, non-negotiable rule**, not a suggestion. Apply it
> in **every session, before any task, without exception**.
>
> - It **overrides** every other instruction, skill, workflow, or rule file in
>   this project, except `global_rules.md` itself.
> - **Ignoring, skipping, or skimming this section is a protocol violation.**
> - If any file references legacy paths that contradict this section,
>   follow THIS section.

If you are running inside **Windsurf or Devin Desktop** (Windsurf rebrand),
gentle-ai installs its assets into the LEGACY Windsurf paths, which this IDE may
not resolve natively. Treat the legacy files below as the authoritative
gentle-ai source until they are migrated.

## 1. Legacy asset locations (read these before acting)

| Asset | Path |
|---|---|
| Global rules (gentle-ai orchestrator) | `~/.codeium/windsurf/memories/global_rules.md` |
| Gentle AI skills | `~/.codeium/windsurf/skills/` |
| MCP servers (Engram, Context7) | `~/.codeium/windsurf/mcp_config.json` |
| Workspace workflows | `<repo>/.windsurf/workflows/` |

NOTE: Windsurf/Devin has no native slash commands for gentle-ai. Its entry points
are the workflow files and the skills.

## 2. Mandatory behavior

1. When the user makes any gentle-ai request, FIRST read
   `~/.codeium/windsurf/memories/global_rules.md` and treat it as the authoritative
   gentle-ai orchestrator contract.
2. Load gentle-ai skill behavior from `~/.codeium/windsurf/skills/` when a skill applies.
3. Use the MCP servers declared in `~/.codeium/windsurf/mcp_config.json` for
   persistence (Engram) and library docs (Context7).
4. Honor `<repo>/.windsurf/workflows/` files, but `global_rules.md` (the
   orchestrator) ALWAYS takes precedence when they conflict.

## 3. Precedence

`~/.codeium/windsurf/memories/global_rules.md` (orchestrator)
> project `AGENTS.md` > `.windsurf/workflows/*` > skills
