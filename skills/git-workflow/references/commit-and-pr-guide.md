# Commit and PR Guide

Conventional commit patterns, PR description templates, and diff analysis techniques.

## Contents

1. [Conventional Commits Quick Reference](#conventional-commits-quick-reference)
2. [Type Selection Guide](#type-selection-guide)
3. [Scope Conventions](#scope-conventions)
4. [Breaking Changes](#breaking-changes)
5. [Multi-line Commit Bodies](#multi-line-commit-bodies)
6. [PR Description Template](#pr-description-template)
7. [Diff Analysis Techniques](#diff-analysis-techniques)

---

## Conventional Commits Quick Reference

Format: `<type>[optional scope][!]: <subject>`

```
feat(auth): add OAuth2 login flow
fix(parser): handle empty input without crash
docs: update API reference for v3 endpoints
refactor!: rename User to Account across codebase
```

Rules:
- Subject line: imperative mood, lowercase first word, no period, max 72 chars
- Body: separated by blank line, wrap at 72 chars, explain what and why (not how)
- Footer: `BREAKING CHANGE: <description>` or `Fixes #123`, `Closes #456`

---

## Type Selection Guide

| Type | When to use | Example |
|------|-------------|---------|
| `feat` | New feature or capability for the user | `feat: add dark mode toggle` |
| `fix` | Bug fix (something was broken, now it works) | `fix: prevent crash on empty input` |
| `docs` | Documentation only (README, comments, docstrings) | `docs: add API usage examples` |
| `style` | Formatting, whitespace, semicolons (no logic change) | `style: fix indentation in config` |
| `refactor` | Code change that neither fixes a bug nor adds a feature | `refactor: extract validation logic` |
| `perf` | Performance improvement | `perf: cache database queries` |
| `test` | Adding or correcting tests | `test: add edge case for parser` |
| `build` | Build system or dependencies | `build: upgrade webpack to v5` |
| `ci` | CI configuration and scripts | `ci: add lint step to pipeline` |
| `chore` | Maintenance tasks (no production code change) | `chore: update .gitignore` |
| `revert` | Reverting a previous commit | `revert: revert "add OAuth2 flow"` |

**Decision flow:**
1. Does it add new user-facing functionality? -> `feat`
2. Does it fix a bug? -> `fix`
3. Does it only change docs? -> `docs`
4. Does it only change formatting? -> `style`
5. Does it improve performance? -> `perf`
6. Does it only change tests? -> `test`
7. Does it change build/deps? -> `build`
8. Does it change CI? -> `ci`
9. Is it a revert? -> `revert`
10. Does it restructure code without changing behavior? -> `refactor`
11. Everything else -> `chore`

---

## Scope Conventions

Scope identifies the affected component. Derive from:

1. **Module/package name**: `feat(auth):`, `fix(parser):`
2. **File area**: `docs(readme):`, `test(e2e):`
3. **Feature area**: `feat(login):`, `fix(checkout):`

Rules:
- Lowercase, no spaces
- Use the most specific scope that still makes sense
- Omit scope if the change spans the entire project
- Monorepo: use package name as scope

---

## Breaking Changes

Two ways to mark:

1. **`!` suffix**: `refactor!: rename User to Account`
2. **Footer**: `BREAKING CHANGE: The User model is now Account`

When to mark as breaking:
- Public API signature changes (parameters added/removed/reordered)
- Configuration format changes requiring user migration
- Database schema changes requiring migration
- Renamed exports, removed public methods
- Changed default behavior

---

## Multi-line Commit Bodies

```
feat(api): add rate limiting to public endpoints

Apply token bucket algorithm with 100 req/min default.
Configurable per-route via RATE_LIMIT_<ROUTE> env vars.

Motivated by production incident on 2024-01-15 where
a single client caused 10x normal load.

Closes #234
```

Body guidelines:
- Explain **why** the change was made, not just what
- Reference issues, incidents, or discussions
- Wrap at 72 characters
- Use blank line between paragraphs

---

## PR Description Template

```markdown
## Summary
- [1-3 bullet points describing what this PR does]

## Changes
### Features
- [feat commits grouped here]

### Fixes
- [fix commits grouped here]

### Other
- [refactor, docs, test, etc.]

## Test Plan
- [ ] [Verification step 1]
- [ ] [Verification step 2]

## Breaking Changes
- [If any, describe migration path]
```

Guidelines:
- Title under 70 characters
- Summary bullets should be understandable without reading the code
- Group changes by conventional commit type
- Test plan should be actionable checklist
- Link to related issues with `Fixes #N` or `Relates to #N`

---

## Diff Analysis Techniques

**Reading diff statistics:**
- `git diff --stat` shows file-level insertions/deletions
- High insertion+deletion in same file = refactoring
- New files with many insertions = new feature
- Deletion-heavy = cleanup or removal

**Identifying change intent:**
- Look at which files changed together (co-change pattern)
- Check test files -- if tests changed, the change is behavioral
- Config-only changes = infrastructure/deployment
- Multiple small changes across files = cross-cutting concern

**Summarizing for PR:**
- Lead with the user-visible outcome
- Group file changes by purpose, not alphabetically
- Call out risks: new dependencies, schema changes, security-relevant code
