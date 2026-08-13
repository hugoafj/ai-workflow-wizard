# Protocol: Commands (catalog + verification)

<!--
  SINGLE SOURCE of truth for the commands catalog rules. Consumed by the Builder
  (command generation), phase2/wf-refresh (missing command verification).
  Source in inventory.md: phase6c/phase6c2 (templates), phase2 19-75, wf-refresh
  684-739, phase8 110. Each command has its template at
  https://github.com/hugoafj/ai-workflow-wizard/tree/main/templates/commands/.
-->

## Commands catalog

| Command | Scope | Skill (1:1) | Template |
|---|---|---|---|
| `/wf-init` | global (install.sh) | ✓ | `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-init/` |
| `/wf-refresh` | global (install.sh) | ✓ | `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-refresh/` |
| `/wf-cleanup` | global (install.sh) | ✓ | `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-cleanup/` |
| `/wf-ladder` | project-specific (Phase 6, LADDER) | ✓ | `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-ladder/` |
| `/wf-tdd` | project-specific (Phase 6, TDD && LAYERS) | ✓ | `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-tdd/` |
| `/wf-orchestrator` | project-specific (Phase 6, ROUTING‖LADDER‖TDD) | ✓ | `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-orchestrator/` |
| `/wf-sdd-trigger` | project-specific (Phase 6, ROUTING) | ✓ | `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-sdd-trigger/` |
| `/wf-onboard` | project-specific (Phase 6) | ✓ | `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-onboard/` |
| `/wf-worktree` | project-specific (Phase 6) | ✓ | `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-worktree/` |
| `/wf-settings` | project-specific (Phase 6) | ✓ | `https://raw.githubusercontent.com/hugoafj/ai-workflow-wizard/main/templates/commands/wf-settings/` |

> Only `/wf-init`, `/wf-refresh`, and `/wf-cleanup` are global (installed with `install.sh`).
> The rest are generated per project in Phase 6 of `/wf-init`.
> **Skill 1:1** — every command in this catalog is also packaged as a SKILL.md: global ones
> by `install.sh` (IDE skill paths + `~/.agents/skills/`), project ones by Builder B4 (native
> per IDE + universal `.agents/skills/<cmd>/SKILL.md` + flat `.agents/protocols/<cmd>.md`).
> `/wf-cicd` was archived (`templates/_archive/wf-cicd/`) — its flow is now the `cicd`
> protocol, consumed by `/wf-settings` (options 9-14) and `/wf-init` Phase 4.7.

## Per-IDE generation

For each command, a variant is generated for each active IDE (`state.answers.ides`),
following the route table format of the `ides` protocol. The command body
is unique (`_base.md` of the command); only the frontmatter/route changes per IDE
(`variants/<ide>.md`).

## Missing commands verification (EXPECTED_COMMANDS)

- `EXPECTED_COMMANDS` is the canonical list of commands that must exist. In phase2
  (upgrade) and wf-refresh, **each file is verified for each active IDE**
  to ensure none are missing — do not assume only Claude Code is active.
- When adding a new command to the workflow: update `EXPECTED_COMMANDS` and the
  watched compatibility terms. It is the source of truth that prevents silent
  missing commands in upgrades (maintenance rule, `workflow` protocol).
