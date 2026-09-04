---
name: branch-pr
description: "Create pull requests with optional issue linkage. Trigger: creating, opening, or preparing PRs for review."
license: MIT
metadata:
  author: "hugoafj"
  version: "1.0"
---

## When to Use

Use this skill when:
- Creating a pull request for any change
- Preparing a branch for submission
- Helping a contributor open a PR

This project-local skill overrides the globally installed `branch-pr` skill for this repository only.

---

## Critical Rules

1. **Treat issue linkage as optional** — do not require, invent, or create an issue solely to open a PR
2. **Every PR MUST have exactly one `type:*` label**
3. **Automated checks must pass**

---

## Workflow

```
1. Create branch: type/description (see Branch Naming below)
2. Implement changes with conventional commits
3. Run project checks before pushing
4. Open PR using the template
5. Add exactly one type:* label
6. Wait for automated checks to pass
```

---

## Branch Naming

Branch names MUST match this regex:

```
^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)\/[a-z0-9._-]+$
```

**Format:** `type/description` — lowercase, no spaces, only `a-z0-9._-` in description.

| Type | Branch pattern | Example |
|------|---------------|---------|
| Feature | `feat/<description>` | `feat/user-login` |
| Bug fix | `fix/<description>` | `fix/zsh-glob-error` |
| Chore | `chore/<description>` | `chore/update-ci-actions` |
| Docs | `docs/<description>` | `docs/installation-guide` |
| Style | `style/<description>` | `style/format-scripts` |
| Refactor | `refactor/<description>` | `refactor/extract-shared-logic` |
| Performance | `perf/<description>` | `perf/reduce-startup-time` |
| Test | `test/<description>` | `test/add-setup-coverage` |
| Build | `build/<description>` | `build/update-shellcheck-config` |
| CI | `ci/<description>` | `ci/add-branch-validation` |
| Revert | `revert/<description>` | `revert/broken-setup-change` |

---

## PR Body Format

### 1. Linked Issue (OPTIONAL)

If a valid GitHub issue exists, reference it:

```markdown
Closes #<issue-number>
```

Valid keywords: `Closes #N`, `Fixes #N`, `Resolves #N` (case insensitive).

If no issue applies, omit this section entirely.

### 2. PR Type (REQUIRED)

Check exactly ONE in the template and add the matching label:

| Checkbox | Label to add |
|----------|-------------|
| Bug fix | `type:bug` |
| New feature | `type:feature` |
| Documentation only | `type:docs` |
| Code refactoring | `type:refactor` |
| Maintenance/tooling | `type:chore` |
| Breaking change | `type:breaking-change` |

### 3. Summary

1-3 bullet points of what the PR does.

### 4. Changes Table

```markdown
| File | Change |
|------|--------|
| `path/to/file` | What changed |
```

### 5. Test Plan

```markdown
- [x] Tests pass
- [x] Manually tested the affected functionality
```

### 6. Contributor Checklist

All boxes must be checked:
- Added exactly one `type:*` label
- Docs updated if behavior changed
- Conventional commit format
- No `Co-Authored-By` trailers

---

## Automated Checks (all must pass)

| Check | What it verifies |
|-------|-----------------|
| PR Has type:* Label | PR has exactly one `type:*` label |
| CI checks | Project-specific automated checks pass |

---

## Conventional Commits

Commit messages MUST match this regex:

```
^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([a-z0-9\._-]+\))?!?: .+
```

**Format:** `type(scope): description` or `type: description`

- `type` — required, one of: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`
- `(scope)` — optional, lowercase with `a-z0-9._-`
- `!` — optional, indicates breaking change
- `description` — required, starts after `: `

Type-to-label mapping:

| Commit type | PR label |
|-------------|----------|
| `feat` | `type:feature` |
| `fix` | `type:bug` |
| `docs` | `type:docs` |
| `refactor` | `type:refactor` |
| `chore` | `type:chore` |
| `style` | `type:chore` |
| `perf` | `type:feature` |
| `test` | `type:chore` |
| `build` | `type:chore` |
| `ci` | `type:chore` |
| `revert` | `type:bug` |
| `feat!` / `fix!` | `type:breaking-change` |

Examples:
```
feat(scripts): add Codex support to setup.sh
fix(skills): correct topic key format in sdd-apply
docs(readme): update multi-model configuration guide
refactor(skills): extract shared persistence logic
chore(ci): add shellcheck to PR validation workflow
perf(scripts): reduce setup.sh execution time
style(skills): fix markdown formatting
test(scripts): add setup.sh integration tests
ci(workflows): add branch name validation
revert: undo broken setup change
feat!: redesign skill loading system
```

---

## Commands

```bash
# Create branch
git checkout -b feat/my-feature main

# Push and create PR (without issue)
git push -u origin feat/my-feature
gh pr create --title "feat(scope): description" --body "## Summary
- What this PR does"

# Push and create PR (with issue)
git push -u origin feat/my-feature
gh pr create --title "feat(scope): description" --body "Closes #N

## Summary
- What this PR does"

# Add type label to PR
gh pr edit <pr-number> --add-label "type:feature"
```
