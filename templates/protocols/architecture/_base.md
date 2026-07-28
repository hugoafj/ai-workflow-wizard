# Protocol: Architecture (AGENTS.md + layers + MCPs)

<!--
  SINGLE SOURCE of truth for the context architecture rules. Consumed by the Builder
  to build AGENTS.router.md and by wf-onboard (MCPs). Source in inventory.md:
  phase6a 5-89 (AGENTS.md structure + Behavior Preferences + MCPs), phase46b 187-191,
  AI_DEV_WORKFLOW 5.1-5.4 / 2.1-2.3 / 7.1-7.3.
-->

## Two layers (don't overlap)

1. **Foundation · gentle-ai** (global, installed per machine): SDD orchestrator, Engram,
   curated skills, multi-IDE routing.
2. **Custom project-specific** (versioned in the repo): AGENTS.md router + satellites +
   commands + packed protocols + hook. This is what this wizard generates.

## AGENTS.md as a thin router

The AGENTS.md no longer contains the heavy embedded mechanism. It contains ONLY:

- **Project-specific content** (adaptable/summarizable to the real stack): `Commands`,
  `Code Style & Conventions`, `Project Structure`, `Critical Constraints`,
  `Testing Approach`, `Programmatic Checks`, `Project MCPs`.
- **Behavior Preferences** (global behavior policies).
- **Routing/detection**: which protocol/skill to load on demand and how (native skills
  for Claude Code; `.agents/protocols/<n>.md` referenced for the rest).
- **Footer `wf-version`** (last line, mandatory — read by /wf-settings and /wf-refresh).

> The flow control mechanism (Decision Ladder, Local Orchestration, TDD Protocol)
> **no longer lives inside AGENTS.md**: it lives in
> `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/protocols/` (decision-ladder, tdd)
> and is packaged as a skill + flat file. The router points to them. This eliminates the
> accumulation of 350-450 lines of mechanism in AGENTS.md.

### What does NOT go in AGENTS.md

Long prose, tutorials, background documentation. AGENTS.md is a lightweight index + router.

## Behavior Preferences (VERBATIM — always written)

- Review gate before commit: show me the full diff and wait for my approval before committing.
- No opportunistic refactor: stick to the new pattern only in new code.
- If you detect that the code contradicts something in this AGENTS.md, report it at the end of
  your response with the tag `[AGENTS.md drift detected: <description>]`. Do not correct AGENTS.md yourself.

## Project MCPs

The MCP table is built according to `state.discovery.stack` and `state.testing`. Fixed base:
Engram (automatic), Context7 (automatic). Conditionals: Playwright (if e2e),
GitHub (if relevant), Supabase/Postgres (if detected), Stripe (if detected).
`/wf-onboard` reads this section to know what to configure on each new machine.

## Programmatic Checks

The `## Programmatic Checks` section lists the commands the agent runs before
declaring a task done (lint + build + test based on `state.testing`).
