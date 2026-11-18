---
name: wf-context-ref
description: >
  Resolve one work reference (ticket, issue, or custom label) and propagate it
  to the session title, branch, PR, commits, and persistent memory
  (Engram or equivalent).
  Trigger: MANDATORY at the start of any work session, when the user mentions a
  ticket/issue/reference, and before creating a branch, opening a PR, committing,
  or saving or updating persistent memory (Engram or equivalent).
version: 0.1.0
---

# Work Context Reference

## Purpose

This skill establishes a single **active reference** for the current work and
tells every later action how to use it.

It is a protocol, not an automation. It does not install hooks, plugins,
adapters, or scripts. It never modifies another skill.

The active reference can be:

- a ticket key (`ITX-2234`, `AM-734`)
- an issue reference (`#123`, `owner/repo#123`)
- a custom label (`auth-refactor`, `q4-migration`)
- any short identifier the user explicitly assigns

No ticket platform is required. No prefix or allowlist is assumed.

## Activation

Load this skill when any of these is true:

- the user mentions a ticket, issue, reference, or work label
- the user starts a work item, asks to create a branch, open a PR, commit, or save memory
- a session has no active reference and work is about to begin

This skill is additive. It does not replace the branch, PR, commit, or memory
skill. It supplies the reference and the format those skills must honor.

## Resolution order

Resolve the active reference in this exact order. Stop at the first match.

1. **Current user message.** An explicit reference in the user's latest message.
2. **Current branch.** A reference embedded in the current git branch name.
4. **Saved state.** The reference stored for this session or worktree.
5. **Ask the user.** Ask once, using the question in "Ask policy".

There is no PR lookup and no other source. If a step produces more than one
distinct candidate, ask which one is primary. Do not guess.

## Detection

Detect references semantically and generically:

- explicit labels in the user's language: "ticket", "issue", "ref", "reference",
  "we are working on", "this is for", or an equivalent phrase
- common shapes such as `ABC-123`, `#123`, `owner/repo#123`, or a URL containing
  a reference
- a short custom label the user explicitly assigns, even if it has no platform
  pattern

Do not treat versions, hashes, dates, file names, or random tokens as references
unless the user explicitly labels them as the work reference. Do not require a
specific prefix. Do not maintain an allowlist.

If the user provides a custom label that is not safe for a branch or title,
confirm the display form and derive a safe form for branch and slug use.

## Ask policy

Ask only when the work is starting and steps 1, 2, and 4 produced nothing.

Ask once per session or worktree, in the user's language:

> Do you want to assign a reference to this work? It can be a ticket
> (`ITX-2234`), an issue (`#123`), or a short label (`auth-refactor`).
> If not, we continue without a reference.

Rules:

- If the user declines, record "no reference" for this session and do not ask
  again unless the user mentions a reference or starts a new work item.
- If the user provides a reference later, adopt it immediately for all subsequent
  actions. Do not rewrite already-created branches, PRs, or memories unless the
  user asks.
- Do not ask during pure questions, code reading, or unrelated tasks.

## Canonical formats

The reference must appear in every artifact below. Apply the format that the host
skill or repository enforces; this section supplies the default. If a stricter
rule exists, adapt the reference to satisfy it and report the adaptation.

### Session title

Target: `<ref>-<current title>`

- If the current title already starts with the reference, leave it unchanged.
- If the current title is empty, use `<ref>`.
- If a different reference is already in the title, ask which one is primary.
  Do not stack references.
- If you can set the session title natively, do it and confirm.
- If you cannot, give the user a ready-to-run command or script for the current
  environment, with the exact target title. Do not hardcode another tool's
  command in this skill. If the environment's rename mechanism is unknown, give
  the user the target title and ask them to apply it. Never claim the title was
  changed if it was not.

### Branch

Default: `<type>/<ref>-<slug>`

- `<type>` comes from the host branch skill or the work type; do not invent a
  new branch convention.
- `<slug>` is lowercase, hyphenated, concise, and derived from the change
  description.
- Preserve the reference's display form unless the repository requires a
  different case or character set. If it does, normalize it and say so.
- If the branch already exists, use it. Do not duplicate the reference.
- If the reference is a GitHub issue and the host skill uses a different branch
  convention, keep the host convention and include the reference in the branch
  in the least invasive way.

### Pull request

Default title: `<type>(<ref>): <description>`

Default body line: `Ref: <ref>`

- If the host PR skill or repository enforces a different title pattern, keep
  that pattern and place the reference where it does not break validation.
- The reference must appear in both the title and the body.
- Do not use `Closes #N` for a non-GitHub reference. If the reference is a
  GitHub issue, the host PR skill may use its own closing syntax.
- If the reference is already present, do not duplicate it.

### Commits

When the host commit skill allows it, use `<type>(<ref>): <description>`.
If the repository's commit rules do not allow a scope, include `Ref: <ref>` in
the commit body instead. Never break the repository's enforced commit format.

### Persistent memory (Engram or equivalent)

Every save, update, or summary for this work must include the reference.

Generic rules (any memory tool):

- Put the reference in the title and in the content. Do not rely only on tags,
  metadata, topic keys, or labels unless the tool's search indexes them.
- Use the memory tool's own save, update, or summary operation. Do not invent a
  tool name that does not exist in the environment.
- If the user declined a reference, do not invent one. Proceed without it.
- If no memory tool is available, skip this section and keep the reference in
  the session state.

Engram-specific rules (when Engram is the memory tool):

- `mem_save` title: `[<ref>] <title>`.
- `mem_save` content: add `Ref: <ref>` as its own line.
- `mem_session_summary`: add `Ref: <ref>` in the `## Goal` section.
- Leave `topic_key` unchanged unless the user explicitly asks for per-reference
  grouping. Do not use `org` for the reference.
- Engram full-text search indexes title and content, not `topic_key` or `org`.
  A reference that exists only in `topic_key` is not searchable.

For another memory tool, apply the generic rules and use its equivalent
title/content fields. Engram is the reference implementation, not a requirement.

## Composition with other skills and memory tools

This skill is the source of the active reference. Other skills and memory tools
consume it.

Before a branch, PR, commit, or memory action (Engram or equivalent):

1. Re-read the active reference from the saved state or the current context.
2. Apply the canonical format, adapted to the host skill's rules.
3. If the host skill already included the reference, leave it as is.
4. If the host skill's rules make the reference impossible, stop and ask.
   Never silently drop it.

This skill never overrides another skill's safety, approval, type, scope, or
repository rules. It only adds the reference.

Other skills do not need to be edited. The agent must carry the active reference
into them and state it in the handoff.

### Standalone mode

If no branch, PR, commit, or memory skill exists, the agent applies the canonical
formats in this skill directly. Do not invent extra conventions. Use the defaults
here unless the repository has explicit rules that require a different format.

## Saved state

State is a small local record, not a script or an adapter. It lets the agent
recover the reference after compaction, resumption, or a later skill handoff.

Location:

- In a git repository: `$(git rev-parse --git-path wf-context-ref)`.
  This is worktree-aware and is not committed.
- Outside git: keep the reference in the conversation. Do not invent a global
  path.

Suggested content:

```json
{"ref":"ITX-2234","branch":"feat/ITX-2234-add-login","source":"user-message"}
```

If the user declines a reference:

```json
{"ref":null,"declined":true,"branch":"feat/ITX-2234-add-login","source":"user-declined"}
```

Rules:

- Read the state at the start of work and before a handoff.
- Write the state only after the reference is explicit or confirmed.
- If the stored branch differs from the current branch, re-resolve. Do not reuse
  a reference from another branch.
- If the user declines a reference, store that decision in the state file so the
  agent does not ask again. If no state file is used, keep the decision in the
  conversation.
- If the user does not want any file writes, skip the state and keep the
  reference in the conversation. Say that it may be lost after compaction.

## Handoff

When another skill or a memory operation (Engram or equivalent) is about to run,
state the active reference and the exact format to use. Example:

> Active reference: ITX-2234. Branch: `feat/ITX-2234-add-login`.
> PR title: `feat(ITX-2234): add login`. Engram title: `[ITX-2234] ...`.

Do not make the user repeat the reference. Do not let a later skill omit it.

## Examples

### Explicit reference in the first message

User: "Let's work on ITX-2234, add login."

- Active reference: `ITX-2234`
- Session title: `ITX-2234-<current title>`
- Branch: `feat/ITX-2234-add-login`
- PR title: `feat(ITX-2234): add login`
- PR body: `Ref: ITX-2234`
- Engram title: `[ITX-2234] ...`

### No reference at the start

User: "Fix the flaky auth test."

- Steps 1, 2, and 4 produce nothing.
- Ask once: ticket, issue, or custom label?
- If the user answers `#482`, use `#482` as the reference.
- If the user answers `auth-refactor`, use `auth-refactor` as the reference.
- If the user declines, proceed without a reference and do not ask again.

### Reference in the branch

Current branch: `fix/AM-734-duplicate-observation`

- Active reference: `AM-734`
- Use it for the session title, PR, commits, and Engram.
- If the repository requires lowercase branches, use `am-734` in the branch
  and keep `AM-734` in the PR title and Engram.

### Reference provided mid-session

User: "By the way, this is for ITX-2234."

- Adopt `ITX-2234` immediately.
- Prefix the session title if possible; otherwise give the user the exact command.
- Use it for all subsequent branches, PRs, commits, and Engram saves.
- Do not rewrite work that was already created unless the user asks.

### Multiple references

User: "Compare ITX-2234 and AM-734."

- Do not pick one.
- Ask which is the primary reference for this work.
- If the work is genuinely about both, use the primary reference for the branch,
  PR, and session title; mention the other in the PR body and Engram content.

### Resumed or compacted session

- Read the saved state first.
- If the stored branch matches the current branch, reuse the reference.
- If the branch changed, re-resolve from the current message or branch.
- If nothing is found, ask once.

## Anti-patterns

- Do not hardcode IDE or CLI commands in this skill.
- Do not require a ticket platform, a prefix, or an allowlist.
- Do not invent a reference or reuse one from another repository.
- Do not modify another skill, plugin, hook, or script.
- Do not look up the PR to resolve the reference.
- Do not put the reference only in metadata the memory tool does not index
  (for Engram: `topic_key` or `org`).
- Do not duplicate a reference that is already present.
- Do not silently drop the reference when a host skill has a stricter format.
- Do not claim a session title was changed when it was not.
