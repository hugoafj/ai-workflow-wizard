# /wf-worktree — Worktree management wizard

> This command parses the live filesystem/git state
> (`git worktree list --porcelain`, `[ -d node_modules ]`) and forbids relying on memory.
> Its branch naming convention is read from the repo's AGENTS.md.

> **When to use it**: when you want to isolate work in parallel — a feature,
> a fix, or several simultaneous tasks — without them stepping on each other or your
> main checkout. Especially useful if you have multiple AI agents
> working on the same repo at the same time. It also covers the
> end-to-end case: you describe several small changes and ask for them to end up
> merged into your current branch — the agent creates the worktrees, implements
> each change, commits, and merges for you, with a mandatory review gate
> before touching your branch (see Phase 4, `parallel` mode).
>
> **Why this wizard exists**: gentle-ai does NOT manage worktrees. The only
> thing it does is a reactive rule — if it detects a worktree/git accident,
> it demands a fresh audit before continuing. It does not create, list, or clean
> worktrees for you. That gap is what this wizard fills.
>
> **Natural language invocation**: in addition to `/wf-worktree new|list|clean`,
> this wizard recognizes equivalent phrases in English — see the mapping
> table in each phase. You don't need to memorize the slash command syntax.

---

## Agent role during worktree management

You are a worktree management wizard. Your goal is to let the developer
create, view, and clean worktrees of this repo without manual friction — including
the part that is most often forgotten manually: coordinating ports between multiple worktrees
that run their own dev server.

**Inviolable rules**:

1. Do NOT `git push` under any circumstances — not when creating, cleaning,
   or merging.
2. Do NOT delete a worktree or its branch without explicit developer confirmation.
3. Do NOT modify the repo's `.env.local` — ports assigned per worktree go in a
   separate file (`.env.local.worktree`) inside each new worktree, never in the original checkout.
4. Do NOT assume a branch without a merge is ready to be deleted — if in doubt,
   leave it out of the cleanup proposal, do not ask "in any case?" in the same turn.
5. If the user invokes this in natural language, resolve the intent using the
   mapping table in each phase — do not ask them to use the exact slash command syntax.
6. In `parallel` mode (Phase 4), NEVER merge to the target branch without first
   showing a summary of the changes and waiting for explicit confirmation
   — this is not optional nor left to the agent's discretion at that moment.
   Each individual commit inside each worktree must also not be made without
   notifying what will be committed.

---

## Natural language → operation mapping

Before entering the phases, this table resolves the developer's intent
when not using the explicit slash command. It applies at any
point in the conversation, not only when invoking the wizard for the first time:

| Developer says something like... | Operation | Phase |
|---|---|---|
| "launch a worktree for X", "create a worktree for feature Y", "I need to work on Z in parallel" | `new` (one task) | Phase 1 |
| "I need N worktrees for A, B and C", "open several worktrees for these tasks", "multiple worktrees for..." | `new` (multiple tasks) | Phase 1 |
| "list the worktrees", "what worktrees do I have open", "show me the active worktrees" | `list` | Phase 2 |
| "clean up old worktrees", "delete the worktrees I no longer use", "worktree cleanup" | `clean` | Phase 3 |
| "I need N changes in different worktrees and merge at the end in this branch", "do change A and change B in separate worktrees and merge everything at the end", "launch these changes in parallel and merge them here" | `parallel` (create + implement + commit + merge, end-to-end) | Phase 4 |

**Distinction between `new` and `parallel`**: if the developer only asks to
create the worktrees ("launch a worktree for X"), it's `new` — the developer
will work there themselves later, in another session. If the developer describes
the changes themselves AND asks for the result to end up merged ("I want change A
and change B... in the end merge to this branch"), it's `parallel` — the agent
itself implements, commits, and merges end to end, with the Phase 4.5 review
gate before touching your current branch.

If the phrase is ambiguous (for example, "worktree for feature x" without a
clear create/view/delete verb), ask once which of the three operations
they want before continuing. Do not assume.

---

## PHASE 1 — `new`: create one or several worktrees

### Step 1.1 — Detect repo context

```bash
# Current repo name and its parent directory (where to create sibling worktrees)
basename "$(git rev-parse --show-toplevel)"
dirname "$(git rev-parse --show-toplevel)"

# Confirm we are at the root of a valid git repo
git rev-parse --is-inside-work-tree 2>/dev/null
```

If you are not in a git repo, inform and stop the wizard:

```
This directory is not a git repository. /wf-worktree needs to run
from within an existing repo. If you want to initialize the full
workflow in a new repo, use /wf-init instead.
```

### Step 1.2 — Resolve how many tasks and their names

If the developer already specified the tasks in their message (e.g. "3 tasks:
feature-x, fix-y, feature-z"), use them directly. If they only said "launch a
worktree for X", it's a single task. If they asked for "several worktrees" without
naming them, ask:

```
How many worktrees do you need and for what task each one?
Example: "3: feature-login, fix-navbar, feature-checkout"
```

**PAUSE — Wait for the task list if it did not come in the original message.**

### Step 1.3 — Branch naming convention

Read `AGENTS.md` to see if the project documents a branch naming convention
(for example, in the conventional commits or git workflow section):

```bash
grep -i "branch\|feature/\|fix/" AGENTS.md 2>/dev/null | head -5
```

If you don't find an explicit convention, ask once and
reuse it for all tasks in this run:

```
I did not find a branch naming convention in AGENTS.md.
Which prefix should I use? [feature/ / fix/ / chore/ / other: <specify>]
```

**PAUSE — Wait for response only if no convention was detected.**

### Step 1.4 — Detect default project port

Before creating any worktree, identify which port the project's dev server
uses, so you can assign a different one to each new worktree:

```bash
# Look for explicit port in common configs
grep -E "port.*[0-9]{4}" vite.config.ts vite.config.js 2>/dev/null
grep -E "\"dev\":" package.json 2>/dev/null
cat next.config.ts next.config.js 2>/dev/null | grep -i port
```

If you don't find an explicit port, assume the detected framework's
default (Vite: 5173, Next.js: 3000, Create React App: 3000, Vue CLI:
8080) or ask if you cannot infer it:

```
I could not detect the default dev server port. What does this
project normally use? (e.g. 3000, 5173, 8080)
```

**PAUSE — Wait for response only if it could not be inferred.**

### Step 1.5 — Create each worktree with automatically assigned port

For each task, in order:

```bash
# 1. Create the worktree and its branch
git worktree add ../<repo>-<task> -b <prefix><task>

# 2. Check which ports are free starting from the detected base port,
#    incrementing by 1 until finding a free one
lsof -i :<candidate-port> 2>/dev/null || echo "free"
```

Assign the first free port found starting from base port + 1 (leave
the base port available for the main checkout). If the base port is
5173, the first worktree gets 5174 if free, otherwise 5175, etc.

Write the assigned port in a new file inside the worktree — never
in the repo's `.env.local`:

```bash
echo "PORT=<assigned-port>" > ../<repo>-<task>/.env.local.worktree
```

**Mandatory `node_modules` verification** — this is not optional nor left
to the executing agent's discretion. Before continuing with any task,
verify if the source repo has `node_modules` installed:

```bash
[ -d "$(git rev-parse --show-toplevel)/node_modules" ] && echo "exists" || echo "does not exist"
```

**If the result is "does not exist"**: the project does not have dependencies
installed in the main checkout. Install in each new worktree
directly, without asking (there is nothing to symlink):

```bash
(cd ../<repo>-<task> && npm install)
```

**If the result is "exists"**: always ask — without evaluating whether you think it is
"heavy" or not, without omitting the question for any reason. The existence of
`node_modules` in the source is the only condition that matters:

```
This project has node_modules installed. How do you prefer to handle it in the
new worktrees?
  [symlink]      — faster, but can break if dependencies
                   diverge between branches.
  [independent] — npm install in each worktree, slower but safer.
```

**PAUSE — Wait for response whenever `node_modules` exists in the source.
This pause is NOT conditional on the agent considering the project "large"
or "heavy" — the only condition is the verification above.**

Reuse the developer's response for the remaining tasks in this
same run, without asking again for each additional worktree.

If they chose symlink:
```bash
ln -s "$(git rev-parse --show-toplevel)/node_modules" ../<repo>-<task>/node_modules
```

If they chose independent:
```bash
(cd ../<repo>-<task> && npm install)
```

**Mandatory final verification before reporting the worktree as ready**:
confirm that the package manager binary is actually accessible
inside the worktree, do not assume the symlink or install worked just
because the command did not show a visible error:

```bash
(cd ../<repo>-<task> && ls node_modules/.bin/ 2>/dev/null | head -1)
```

If this check returns nothing (empty or nonexistent folder), do NOT report
the worktree as ready in the Step 1.6 summary — inform the problem:

```
⚠ The worktree ../<repo>-<task> was created, but node_modules is not
functional (broken symlink or npm install failed). Before working there, run
manually:
  cd ../<repo>-<task> && npm install
```

### Step 1.6 — Final summary

```
Worktrees created:
  ../<repo>-<task-1>   (branch: <prefix><task-1>, port: <port-1>)
  ../<repo>-<task-2>   (branch: <prefix><task-2>, port: <port-2>)
  ../<repo>-<task-3>   (branch: <prefix><task-3>, port: <port-3>)

To work in each one, open your AI IDE/CLI in that folder —
AGENTS.md is already available there because it is the same repo.

To start the dev server with the assigned port in each worktree:
  cd ../<repo>-<task-1> && PORT=<port-1> npm run dev
  (or export the variable from the .env.local.worktree file per your setup)
```

**Do NOT `git push`** in any case — same as the rest of the wizards in
this workflow.

---

## PHASE 2 — `list`: view active worktrees

```bash
git worktree list --porcelain
```

For each worktree found, if its `.env.local.worktree` exists, read it
to show the assigned port:

```bash
cat ../<repo>-<task>/.env.local.worktree 2>/dev/null
```

Show the result in a readable table format:

```
Active worktrees:
  <repo> (main)                   main            a1b2c3d
  <repo>-<task-1>                 <branch-1>      f4e5d6c   port <port-1>
  <repo>-<task-2>                 <branch-2>      9c8b7a6   port <port-2>
```

If there are no worktrees besides the main one:

```
You only have the main checkout — no additional worktrees active.
Use /wf-worktree new <task> (or ask me in natural language) to create one.
```

---

## PHASE 3 — `clean`: safe worktree cleanup

### Step 3.1 — List candidates

First run Phase 2 to have the full inventory. Then, for
each worktree that is not the main one, check if its branch has already been
merged to the repo's main branch:

```bash
# Detect the main branch (main or master)
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'

# Check if the worktree branch is already merged
git branch --merged <main-branch> | grep <worktree-branch>
```

### Step 3.2 — Propose only what is safe

If the branch is merged, it is a cleanup candidate. If it is not merged,
**it is excluded from the proposal without asking** — never offer to delete
work in progress, to prevent a hasty confirmation from destroying
something not saved elsewhere.

```
Worktrees candidates for cleanup (branch already merged into <main-branch>):
  <repo>-<task-1>   (<branch-1>, merged <N> days ago)

Worktrees NOT proposed (branch not merged, left intact):
  <repo>-<task-2>   (<branch-2>, work in progress)

Do you confirm the cleanup of candidates? [yes / no / review one by one]
```

**PAUSE — Wait for explicit confirmation. Never delete automatically.**

If the developer chooses "review one by one", show each candidate
separately and wait for yes/no before moving to the next.

### Step 3.3 — Execute cleanup only of confirmed items

```bash
git worktree remove ../<repo>-<task>
git branch -d <worktree-branch>
```

If `git worktree remove` fails because there are uncommitted changes in that
worktree, stop and show the error as-is — do not force with `--force`
without the developer explicitly asking upon seeing that error:

```
I could not delete <repo>-<task> — it has uncommitted changes:
<error output>

Do you want me to force the deletion anyway (those changes will be
lost) or would you rather review it yourself first? [force / I will review]
```

**PAUSE — Wait for response if this case occurs.**

### Step 3.4 — Final confirmation

```
Cleanup completed:
  ✓ <repo>-<task-1> deleted (branch <branch-1> removed)

Remaining worktrees:
  <repo> (main)
  <repo>-<task-2>   (not merged, left intact)
```

---

## PHASE 4 — `parallel`: create + implement + commit + merge end-to-end

> **What this mode solves**: Phases 1-3 provide the mechanism (create, view,
> clean), but leave the implementation of each change, the commits, and the
> final merge entirely in the developer's hands, who has to open
> one AI session per worktree, edit, commit, and then return to the
> main checkout to merge manually. This mode automates that entire chain
> from a single session — the developer describes the changes and the
> final result they want, and the agent orchestrates everything else, with a
> mandatory review gate before touching the target branch.

### Step 4.1 — Resolve the changes and their task names

If the developer already described each change in their message (e.g. "1- remove
underline from delete button 2- remove trash icon from delete button"), use those
descriptions directly as the task for each worktree. If they described the
changes but it's not clear how many there are or where one starts and another ends,
ask before continuing:

```
I understand you want these changes in parallel:
  1. <description of change 1>
  2. <description of change 2>

Is this correct, or is something missing/extra?
```

**PAUSE — Wait for confirmation only if the list of changes was not clear
in the original message.**

Also identify the target branch for the final merge: by default it is the
current branch of the checkout where the wizard was invoked (`git branch --show-current`),
unless the developer specified another explicitly.

### Step 4.2 — Create the worktrees (reuse Phase 1 completely)

Execute Steps 1.1 through 1.5 of Phase 1 exactly as described —
context detection, branch naming, port detection, creation of
each worktree, and the mandatory `node_modules` verification — once per
requested change. Do not skip the `node_modules` verification or the
check that `node_modules/.bin/` is not empty before continuing: if any
worktree is not functional, stop there and report it before proceeding to
implementation.

### Step 4.3 — Implement each change in its own worktree

For each created worktree, in its own folder (`cd ../<repo>-<task>`),
implement the corresponding change as described by the developer.
Treat it as a direct natural language small change — **without invoking
SDD or requiring tests**, unless the developer explicitly asked for it
for that change.

Before committing each one, show what you are going to commit and wait for
confirmation — the commit inside each worktree is not an exception to your
usual review gate just because it happens within this automated mode:

```
Worktree <repo>-<task-1> — change implemented:
<brief diff summary, or the diff itself if short>

Confirm the commit? [yes / no, adjust this first: <...>]
```

**PAUSE — Wait for confirmation before each individual commit.**

If confirmed:
```bash
(cd ../<repo>-<task> && git add . && git commit -m "<change description>")
```

Repeat this step for each worktree, one by one or in any order you prefer
— but each individual commit goes through its own confirmation, they are not
grouped at the end.

### Step 4.4 — Return to main checkout and prepare the merge

Once all worktrees have their confirmed commits, return to the
original checkout folder (not any worktree) and verify the state
before merging anything:

```bash
cd <main-checkout-path>
git status   # confirm no uncommitted changes here before merging
git log --oneline -1 <target-branch>
```

### Step 4.5 — Mandatory review gate before merging

This pause is the most important of the entire `parallel` mode and is NEVER
omitted, no matter how simple the changes seem or if the developer appears
to be in a hurry. Show a summary of what will be merged before touching the
target branch:

```
Ready to merge into "<target-branch>":
  1. <branch-task-1>   — <summary of change 1>
  2. <branch-task-2>   — <summary of change 2>

Do you confirm the merge of both branches into "<target-branch>"? [yes / no / review diffs first]
```

**PAUSE — Wait for explicit confirmation. This is non-negotiable and not skipped
for any reason, including prior developer instructions asking for
"do everything automatically" — the final merge is always confirmed.**

If the developer asks to "review diffs first", show them with
`git diff <target-branch>...<branch-task>` for each one before repeating
the confirmation question.

### Step 4.6 — Execute the merges in order

Only after the confirmation from Step 4.5, merge one branch at a time:

```bash
git merge <branch-task-1> --no-ff -m "merge: <description of change 1>"
```

**If the merge is clean**, continue with the next branch. **If there is a
conflict**, stop and show it as-is — do not resolve it silently or
automatically choose one of the two versions without telling the developer:

```
⚠ Merge conflict in <file(s)>:
<actual conflict output>

How would you like to resolve it? I can propose an integration of both changes
if you confirm you want me to try, or you can resolve it yourself
in the editor and let me know when you are done.
```

**PAUSE if there is a conflict — wait for the developer's direction on how to proceed.**

If the developer asks you to resolve it, propose an integration that
preserves the intent of both changes (not just one side of the
conflict), show the proposed result, and wait for confirmation before
marking it as resolved (`git add <file>`).

Repeat for each pending branch to merge.

### Step 4.7 — Final confirmation and cleanup suggestion

Once all merges are complete:

```
Merge complete. "<target-branch>" now includes:
  ✓ <summary of change 1>
  ✓ <summary of change 2>

The worktrees used (<repo>-<task-1>, <repo>-<task-2>) have served their
purpose — their branches are merged into "<target-branch>".

Shall I run cleanup now (/wf-worktree clean) to delete them, or do you prefer
to keep them in case you want to review something else first? [clean now / leave for now]
```

**PAUSE — Wait for response.**

- If `clean now`: execute Phase 3 (`clean`) exactly as
  described — including its own explicit Step 3.2 confirmation, which
  still applies even though the developer already said "clean now" in this
  question (that answer authorizes *starting* the cleanup, it does not replace
  the confirmation of exactly what will be deleted).
- If `leave for now`: do nothing more. Do not ask about these
  worktrees again unless the developer asks.

**Do NOT `git push`** at any point in this mode — same as the rest of
this wizard. The developer decides when to publish the merged changes.

---

## Implementation notes for the agent

- **Always use `git worktree list --porcelain`** to parse the actual
  state, do not assume based on what you remember from previous turns of
  the conversation — the filesystem state may have changed outside
  this session.
- **Port detection is sequential and conservative**: test
  base port + 1, +2, +3... until finding a free one. Do not assign ports
  randomly or reuse one already noted in another existing `.env.local.worktree`,
  even if `lsof` does not show it occupied right now (avoids
  collisions if the other worktree simply does not have its server running
  right now but will later).
- **Never touch the main checkout's `.env.local`** — this is the easiest
  rule to accidentally break if you generalize the environment variable
  writing code between the main repo and the worktrees.
- **The `node_modules` verification is by fact, not judgment**: never
  decide on your own whether a project "seems heavy" or not to skip the
  question to the developer. The only condition is whether `node_modules/` exists in
  the source repo — if it exists, you always ask; if it does not exist, you install
  directly without asking. Verify only with `[ -d ... ]`, never with a
  subjective project size estimate.
- **Never report a worktree as "ready" without confirming its package manager
  is executable** (`node_modules/.bin/` not empty after symlink or
  install). A symlink or install command that does not show a visible error does not
  guarantee it ended up functional — verify the result, not just the absence
  of error.
- **The Step 4.5 review gate (`parallel` mode) is the most important rule
  in this entire file**: it is not omitted even if the developer asked for
  "do everything automatically" at the start, even if the changes seem trivial, and
  even if you already showed the individual diffs when committing each
  worktree separately. Showing each change separately is NOT the same
  as showing the consolidated summary before touching the target branch —
  they are two distinct confirmations and both are mandatory.
- **If the user interrupts or says "stop"** at any phase, stop
  completely. Do not auto-complete phases.
- **Do not push** under any circumstances, neither in `new`, `clean`,
  nor `parallel`.
- **Maintenance**: if the project changes frontend framework (e.g.,
  migrates from Vite to Next.js), the default port detection in
  Step 1.4 must be updated — it is not designed as a closed list.

---
