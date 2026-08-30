**Register Playwright MCP** (only if the user activated layer 3) — adds the MCP to the active agent's configuration. The Playwright MCP is `@playwright/mcp` and allows the agent to launch browsers during sdd-apply and sdd-verify.

---

### OpenCode (`.opencode/mcp.json`)

OpenCode uses a `mcp` key with `type: local` and `command` array:

```json
{
  "mcp": {
    "playwright": {
      "type": "local",
      "command": ["npx", "@playwright/mcp"]
    }
  }
}
```

---

### Claude Code (`.claude/settings.json` or `.claude/settings.local.json`)

Use `.claude/settings.local.json` to avoid committing if it has an API key:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp"]
    }
  }
}
```

---

### Cursor (`.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp"]
    }
  }
}
```

---

### Windsurf — GLOBAL ONLY (`~/.codeium/windsurf/mcp_config.json`)

⚠️ **IMPORTANT**: Windsurf does NOT support project-level MCP configuration. The MCP must be registered globally in `~/.codeium/windsurf/mcp_config.json`. Do NOT write `.windsurf/mcp.json` in the project — it will be ignored.

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp"]
    }
  }
}
```

---

### Other agents

For any other agents configured in this project, check each one's MCP registration format. If the format is unclear for any agent, report to the user which files to create and with what content, and wait for confirmation before writing.

---

### Notes

- `@playwright/mcp` needs no API key — it is reasonable to commit the project-level configs (OpenCode, Cursor, Claude) so the whole team has them.
- For Windsurf, each team member must run the global registration once, or the project docs should include the global config snippet.
- The wizard's Phase 8.1e will attempt to write project-level configs for all IDEs EXCEPT Windsurf (global only).