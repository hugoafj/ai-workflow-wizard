# sdd-lite

Initiate the SDD Lite flow for the next task.

Run sdd-propose → sdd-tasks → sdd-apply.
No formal spec (sdd-spec), no design.md (sdd-design).
Wait for proposal approval before generating tasks.
Wait for task approval before implementing.

The user chose SDD Lite consciously.
Do not ask if they prefer full SDD — they already know.
Do not ask if they prefer direct implementation — they already know.

## SDD skill discovery

The SDD skills (sdd-propose, sdd-tasks, sdd-apply, tdd-protocol, sdd-archive)
are **global** — gentle-ai installed them in your home, NOT in the project.

**Location per IDE:**
- Claude Code: `~/.claude/skills/sdd-propose/SKILL.md` (etc.)
- Windsurf: `~/.codeium/windsurf/skills/sdd-propose/SKILL.md` (etc.)
- Cursor: `~/.cursor/skills/sdd-propose/SKILL.md` (etc.)
- OpenCode: `~/.config/opencode/skills/sdd-propose/SKILL.md` (etc.)
- Kiro: `~/.kiro/skills/sdd-propose/SKILL.md` (etc.)

If you can't find the skills in those paths, use `find` or `glob` to search
for `**/sdd-propose/SKILL.md` in the user's home.

Do NOT search for `sdd-propose` in the project directory — it does not exist there.

## Execution mode

Delegate each phase to the corresponding sub-agent using your native
delegation mechanism (`task()`, `spawn_agent()`, `run_subagent()`, or whatever
your IDE supports). Each IDE has its own mechanism — use it.

sdd-apply is HEADLESS (it executes and returns, it cannot ask you). Therefore,
after approving tasks, YOU (orchestrator) issue the 🧪 TDD PROPOSAL covering
the tasks in batch and wait for the user's coverage choice BEFORE
delegating to sdd-apply. Only then delegate with the decision baked into the
prompt (e.g. "coverage: unit + integration + e2e") and inject the
tdd-protocol under a "## Skills to load before work" block so the
sub-agent executes the RED→GREEN cycle per task and shows the --headed command
if it generates E2E specs. In strict mode there is no proposal (delegate directly;
sdd-apply enforces via strict_tdd: true).

When sdd-apply finishes, with tests/checks green, SUGGEST to the user
to run sdd-archive as cleanup (it moves the change to openspec/changes/archive/;
do not run it on your own and it requires explicit user approval).