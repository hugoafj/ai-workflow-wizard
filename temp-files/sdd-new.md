---
description: Start a new feature with SDD (modern contract) for Cascade in Windsurf/Devin
---

# /sdd-new

This workflow defines the mandatory behavior of **Cascade** when starting a new feature, medium/large scope change, or work with enough uncertainty to require formal planning.

## Purpose

Execute `/sdd-new` with the modern gentle-ai contract:

- **Orchestrator as authority**: read `~/.codeium/windsurf/memories/global_rules.md` FIRST and treat it as the authoritative contract.
- **Plan Mode** for planning (never code before approval)
- **Artifact store** according to orchestrator policy: `engram` (default) | `openspec` | `hybrid` | `none`. This project declares **{{sdd.backend}}** (see AGENTS.md).
- **Code Mode** only after explicit user approval

**This workflow does NOT create `.sdd/`.** The `.sdd/` directory is the LEGACY Windsurf format, obsolete. If the orchestrator, a skill, or an instruction mentions `.sdd/`, IGNORE it.

## When to use this workflow

Activate this workflow whenever any of these conditions occur:

- The user starts a **new feature**
- The task affects **multiple files or modules**
- The change has **architectural risk** or uncertainty
- The user explicitly asks to work with **SDD**
- The implementation requires a formal contract before writing code

If the task is small, specific, or clearly minor maintenance, this workflow is NOT the right path (use direct Code Mode).

---

## Mandatory sequence

### 0. Read the orchestrator (AUTHORITATIVE)

Read `~/.codeium/windsurf/memories/global_rules.md` in full. This contract rules over everything that follows. In particular: SDD Init Guard, Execution Mode, Artifact Store Mode, Delivery Strategy, and Approval Gates.

### 1. SDD Init Guard (MANDATORY, silent)

Before executing `/sdd-new`, check whether `sdd-init` has run for this project:

1. `mem_search(query: "sdd-init/{project}", project: "{project}")`
2. If it appears → init done, continue normally.
3. If it does NOT appear → run the `sdd-init` phase **inline FIRST**, and only then continue with `/sdd-new`.

**Do NOT ask permission, do NOT stop**: run init silently if needed. This guarantees detection of test capabilities, strict TDD, and project context.

### 2. Determine and cache session options

The first time in the session, resolve and cache:

- **Execution Mode**: ask `Automatic` (default) vs `Interactive`. In Windsurf, `Interactive` is the natural behavior via Approval Gates; `Automatic` skips gates and runs everything sequentially.
- **Artifact Store Mode**: ask `engram` | `openspec` | `hybrid` | `none`. If the user does not specify, detect: engram available → `engram`; otherwise → `none`. **This project declares `{{sdd.backend}}`** in AGENTS.md, so the choice must start from there.
- **Delivery Strategy**: ask `ask-on-risk` (default) | `auto-chain` | `single-pr` | `exception-ok`.

Cache the three for the session. Do not ask again unless explicitly requested.

### 3. Enter Plan Mode

Enter **Plan Mode** immediately. Analyze the request, formulate the high-level plan, identify scope, risks, dependencies, and likely files.

Prohibited at this stage:

- DO NOT write production code
- DO NOT enter Code Mode
- DO NOT modify application logic
- DO NOT run partial implementation "to get ahead"
- DO NOT assume implicit approval

### 4. Recover context

Before drafting any SDD artifact, recover architectural context and project constraints:

1. **Engram** via MCP: `mem_search` for previous decisions and `mem_context` for recent context
2. Read the orchestrator (`global_rules.md`) if not yet in context
3. Read the project `AGENTS.md`
4. Load the SDD skills from `~/.codeium/windsurf/skills/sdd-*/SKILL.md` when the phase requires them

Search, at minimum: previous architectural decisions, repo conventions, constraints, quality rules, established patterns.

If there is not enough context, say so explicitly in the plan. **Do not invent conventions.**

### 5. Explore phase (inline)

Execute the `sdd-explore` phase inline: investigate the codebase for this change, compare approaches, without creating files. Save the `explore` artifact in the active store:

- **engram**: topic key `sdd/{change-name}/explore`
- **openspec**: `openspec/changes/<change-name>/exploration.md`

Present the exploration summary to the user.

### 6. Propose phase (inline)

Execute the `sdd-propose` phase inline to create the proposal from the exploration. Save the `proposal` artifact in the active store:

- **engram**: topic key `sdd/{change-name}/proposal`
- **openspec**: `openspec/changes/<change-name>/proposal.md`

Use the change name passed by the user (`$ARGUMENTS`). If no name was given, propose one in kebab-case and confirm it.

#### Minimum proposal content

- Change title
- Problem to solve
- Objective
- Included / excluded scope
- Proposed approach
- Main risks
- Open assumptions
- Pending questions or decisions

**Do NOT create `.sdd/` nor `.sdd/proposal.md` nor `.sdd/spec.md` under any circumstance.**

### 7. Present summary and Approval Gate

Present a brief summary of the proposal (objective, scope, risks) and stop **ABSOLUTELY**.

Ask exactly:

**Do you approve this implementation plan?**

- Wait for explicit confirmation (yes / approved / agree / go ahead / equivalent)
- Do NOT continue to Code Mode without approval
- Do NOT interpret silence as approval
- If the user asks for changes: adjust the proposal, present again, ask again

### 8. After approval

With the proposal approved, continue with the remaining phases (`spec`, `design`, `tasks`) via `/sdd-continue` or `/sdd-ff`, according to Execution Mode. Only then, and after the approval gate is passed, switch to Code Mode for `apply`.

---

## Explicit prohibitions

While this workflow has not been approved by the user:

- DO NOT write production code
- DO NOT edit implementation files
- DO NOT run application tasks
- DO NOT switch to Code Mode
- DO NOT create commits
- DO NOT run partial implementation
- DO NOT automatically continue to the next SDD step
- DO NOT create the `.sdd/` directory nor its artifacts (legacy obsolete format)

---

## Exit criteria for this workflow

This workflow is considered correctly executed only if:

- It read the orchestrator (`global_rules.md`) as authority
- It applied the SDD Init Guard (running `sdd-init` inline and silently if missing)
- It resolved and cached Execution Mode, Artifact Store Mode, and Delivery Strategy
- It used **Plan Mode**
- It recovered context with **Engram**, the orchestrator, or `AGENTS.md`
- It executed `sdd-explore` and `sdd-propose` inline in that order
- It saved the proposal in the active store (this project: `{{sdd.backend}}/changes/<name>/proposal.md`)
- It presented the summary and asked exactly: **Do you approve this implementation plan?**
- It stopped to wait for explicit approval
- It did NOT create `.sdd/` at any point

If any of these points do not occur, the workflow was executed incorrectly.
