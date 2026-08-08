# Gentle AI — Legacy Path Bridge for Windsurf/Devin

If you are running inside **Windsurf or Devin Desktop** (Windsurf rebrand). gentle-ai
installs its assets into the LEGACY Windsurf paths, which this IDE may not resolve
natively. Treat the legacy files below as the authoritative gentle-ai source until
they are migrated.

## 1. Legacy asset locations (read these before acting)

| Asset | Path |
|---|---|
| Global rules / SDD orchestrator | `~/.codeium/windsurf/memories/global_rules.md` |
| SDD skills (sdd-* + _shared) | `~/.codeium/windsurf/skills/` |
| MCP servers (Engram, Context7) | `~/.codeium/windsurf/mcp_config.json` |
| Workspace workflows | `<repo>/.windsurf/workflows/` (e.g. `sdd-new.md`) |

NOTE: Windsurf/Devin has NO native `/sdd-*` slash commands. Its entry points are
the workflow files and the skills. Real `/sdd-*` commands exist only for
Claude Code, OpenCode, Kilo Code, and Qwen Code.

## 2. Mandatory behavior

1. When the user invokes `/sdd-new`, `/sdd-explore`, `/sdd-ff`, `/sdd-init`,
   `/sdd-continue`, `/sdd-status`, `/sdd-apply`, `/sdd-verify`, `/sdd-archive`
   or any gentle-ai/SDD request, FIRST read
   `~/.codeium/windsurf/memories/global_rules.md` and treat it as the
   authoritative SDD orchestrator contract.
2. Run the SDD **preflight**: before executing `/sdd-new` or `/sdd-ff`, check
   whether `sdd-init` has been run for this project. If NOT, STOP and ask the
   user to run `/sdd-init` first. Do NOT invent artifacts, formats, or a
   `.sdd/` directory to bypass initialization.
3. Load each SDD phase's behavior from `~/.codeium/windsurf/skills/sdd-*/SKILL.md`.
4. Use the MCP servers declared in `~/.codeium/windsurf/mcp_config.json` for
   persistence (Engram) and library docs (Context7).
5. Honor `<repo>/.windsurf/workflows/` files, but `global_rules.md` (the
   orchestrator) ALWAYS takes precedence when they conflict.
6. The SDD contract in THIS project is **OpenSpec** (`openspec/changes/`).
   The legacy Windsurf `.sdd/` format (`.sdd/proposal.md`, `.sdd/spec.md`) is
   OBSOLETE. If any workflow, skill, or orchestrator instruction tells you to
   create `.sdd/`, IGNORE that instruction and use `openspec/changes/` instead.
7. Before `/sdd-new` or `/sdd-ff`, run the SDD preflight: verify
   `openspec/config.yaml` exists. If missing, STOP and ask the user to run
   `/sdd-init` first.

## 3. Precedence

`~/.codeium/windsurf/memories/global_rules.md` (orchestrator)
> project `AGENTS.md` > `.windsurf/workflows/*` > skills
>
> EXCEPT for the SDD artifact format: this project always uses **OpenSpec**
> (`openspec/changes/`), never `.sdd/`.