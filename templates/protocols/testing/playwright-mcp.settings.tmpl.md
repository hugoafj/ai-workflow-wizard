**Register Playwright MCP** (only if the user activated layer 3) — adds the MCP to the active agent's configuration. The Playwright MCP is `@playwright/mcp` and allows the agent to launch browsers during sdd-apply and sdd-verify.

For Claude Code, the MCP is registered in `.claude/settings.json` (or `.claude/settings.local.json` to avoid committing it if it has an API key):

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

For other agents configured in this project, check each one's MCP registration format (Cursor: `.cursor/mcp.json`, Windsurf: `.windsurf/mcp.json`). If the format is unclear for any agent, report to the user which files to create and with what content, and wait for confirmation before writing.
