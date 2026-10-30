---
name: wf-conventional-pr
description: "Create pull requests for projects that use Conventional Commits and release-please. Trigger: creating, opening, or preparing PRs for review."
license: MIT
metadata:
  author: "hugoafj"
  version: "2.0"
---

## When to Use

Use this skill when:
- Creating a pull request for any change
- Preparing a branch for submission
- Helping a contributor open a PR

---

## Critical Rules

1. **Issue linkage is optional**: do not require, invent, or create an issue solely to open a PR
2. **Every PR MUST have exactly one `type:*` label**
3. **Commit messages and PR titles follow Conventional Commits**: release-please reads them to build the changelog and decide releases
4. **Required checks must pass** before merge

---

## Workflow

```
1. Create branch: type/description (see Branch Naming below)
2. Implement changes with Conventional Commits
3. Run project checks before pushing
4. Open PR using the template
5. Add exactly one type:* label
6. Wait for required checks to pass
```

---

## Branch Naming

```
^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)\/[a-z0-9._-]+$
```

Format: `type/description`, lowercase, only `a-z0-9._-` in the description.

| Type | Example |
|------|---------|
| Feature | `feat/user-login` |
| Bug fix | `fix/null-session-token` |
| Chore | `chore/update-ci-actions` |
| Docs | `docs/install-guide` |
| Refactor | `refactor/extract-auth-helpers` |

---

## Release Impact

release-please turns commits into releases. By default:

| Commit type | Release | Changelog |
|-------------|---------|-----------|
| `feat` | yes (feature bump) | Features |
| `fix`, `perf`, `revert` | yes (fix bump) | Bug fixes, performance, reverts |
| `refactor`, `docs`, `chore`, `test`, `build`, `ci`, `style` | no | hidden |
| `feat!`, `fix!`, or a `BREAKING CHANGE:` footer | yes (major bump) | Breaking changes |

Check the project's `release-please-config.json` (`changelog-sections`) before relying on this table: a project can change what is visible.

---

## PR Body Format

### 1. Linked Issue (OPTIONAL)

If a valid issue exists, reference it. Valid keywords: `Closes #N`, `Fixes #N`, `Resolves #N`.
If no issue applies, omit this section entirely.

### 2. Type (REQUIRED)

Check exactly ONE and add the matching label:

| Checkbox | Label |
|----------|-------|
| Bug fix | `type:bug` |
| New feature | `type:feature` |
| Documentation only | `type:docs` |
| Refactoring | `type:refactor` |
| Maintenance/tooling | `type:chore` |
| Breaking change | `type:breaking-change` |

### 3. Summary

1-3 bullets: what the PR does and why.

### 4. Changes

| File | Change |
|------|--------|
| `path/to/file` | What changed |

### 5. Test Plan

- [ ] Tests pass
- [ ] Manually tested the affected functionality

### 6. Contributor Checklist

- [ ] Exactly one `type:*` label
- [ ] Docs updated if behavior changed
- [ ] Conventional Commit title and commits
- [ ] No `Co-Authored-By` trailers

---

## Conventional Commits

```
^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([a-z0-9\._-]+\))?!?: .+
```

Format: `type(scope): description` or `type: description`. A `!` after the type marks a breaking change.

| Commit type | PR label |
|-------------|----------|
| `feat` | `type:feature` |
| `fix`, `revert` | `type:bug` |
| `docs` | `type:docs` |
| `refactor` | `type:refactor` |
| `perf` | `type:feature` |
| `chore`, `style`, `test`, `build`, `ci` | `type:chore` |
| `feat!` / `fix!` | `type:breaking-change` |

Examples:
```
feat(search): add fuzzy matching to the query box
fix(auth): prevent session timeout on refresh
docs(readme): document the configuration file
refactor(api): extract shared validation
chore(ci): pin the lint action version
feat!: replace the config format with TOML
```

---

## Automated Checks

| Check | What it verifies |
|-------|------------------|
| PR has type:* label | Exactly one `type:*` label (when the project installs the label check) |
| Commit lint | Commit messages match the Conventional Commits pattern (commitlint, when installed) |
| CI checks | Project-specific checks pass |

---

## Commands

```bash
git checkout -b feat/my-feature main
git push -u origin feat/my-feature
gh pr create --title "feat(scope): description" --body "## Summary
- What this PR does"
gh pr edit <pr-number> --add-label "type:feature"
```
