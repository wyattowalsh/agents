# Wave 0 Triage Protocol

Scan the project, analyze git history, stratify risk, and assemble context before any reviewer touches code.
Run as the first action in every Mode 2 full codebase audit.

## Contents

- [Project Scanning](#project-scanning)
- [Git History Analysis](#git-history-analysis)
- [Risk Stratification](#risk-stratification)
- [Context Assembly](#context-assembly)
- [Triage Output Template](#triage-output-template)

## Project Scanning

Invoke the scanner to generate a structured JSON project profile:

```bash
uv run scripts/project-scanner.py [path]
```

Detected fields: language(s), framework(s), build system, test framework, package manager, file count, LOC per file, max nesting depth, and estimated cyclomatic complexity (max/mean per file).

If the scanner is unavailable, gather equivalent data manually:

```bash
find [path] -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -15   # files by extension
find [path] -type f \( -name '*.py' -o -name '*.ts' -o -name '*.go' \) | xargs wc -l | sort -rn | head -20  # LOC
ls [path]/package.json [path]/pyproject.toml [path]/Cargo.toml [path]/go.mod 2>/dev/null  # package managers
```

### Convention File Detection

Check for AI agent instruction files — review against project's own conventions:

```bash
ls [path]/AGENTS.md [path]/CLAUDE.md [path]/GEMINI.md [path]/.cursorrules [path]/.github/copilot-instructions.md 2>/dev/null
```

If found, include in triage context. Reviewers should validate:

- Code follows conventions declared in these files
- New code doesn't introduce patterns explicitly prohibited by project rules
- Agent-specific configurations are consistent across files

### Monorepo Workspace Detection

Detect workspace structures for review scope management:

```bash
# Node workspaces
cat [path]/package.json | jq '.workspaces // empty'
# Python workspaces (uv)
grep -A5 '\[tool.uv.workspace\]' [path]/pyproject.toml
# Rust workspaces
grep -A5 '\[workspace\]' [path]/Cargo.toml
# Go workspaces
cat [path]/go.work 2>/dev/null
```

For monorepo reviews:

- Scope each reviewer to their workspace package boundaries
- Flag cross-package imports that bypass workspace boundaries
- Adjust review depth per package based on independent risk stratification

## Git History Analysis

Spawn four parallel haiku subagents, one per dimension, in a single message. Collect all results before proceeding to risk stratification.

**Hot files** -- 20 most frequently changed files in 90 days (top 10% = high-churn):

```bash
git log --since="90 days ago" --name-only --pretty=format: | sort | uniq -c | sort -rn | head -20
```

**Blame density** -- for each hot file, count distinct authors (5+ authors = higher risk):

```bash
git shortlog -s -n -- [file]
```

**Recent changes** -- files changed in last 2 weeks get priority boost (overrides historical churn):

```bash
git log --since="14 days ago" --name-only --pretty=format: | sort -u
```

**Related issues** -- open bugs in touched areas indicate known instability:

```bash
gh issue list --state open --limit 50 --json title,number,labels,body
```

Cross-reference issue titles/bodies against hot file paths. Elevate matching files to HIGH risk.

## Risk Stratification

Assign every in-scope file to a tier using scanning metrics and git signals.

**HIGH** -- any trigger fires: touches auth/payments/crypto/user-data/external-I/O; max nesting >= 5; top 10% churn; LOC > 300; 5+ authors; open bugs referencing the file.
Route: deep specialist review with research validation. Activate context-dependent checklists (security, resilience, data migration as applicable).

**MEDIUM** -- no HIGH trigger, but any of: business logic, data models, or API handlers; moderate complexity (nesting 3-4, LOC 50-300); above-median churn; 2-4 authors.
Route: standard review at all three levels. Research-validate non-obvious findings only.

**LOW** -- all of: config/docs/static assets/simple utilities; LOC < 50; below-median churn; 1-2 authors; no open issues.
Route: quick scan only. Flag obvious defects. Skip deep analysis and creative lenses.

## Classification Gating — Review Depth

After risk stratification, compute a review depth score (0-10) to determine how deep the review should go. This prevents over-reviewing simple changes and under-reviewing complex ones.

| Factor                               | Points |
| ------------------------------------ | ------ |
| File count: 1-2                      | 0      |
| File count: 3-5                      | 1      |
| File count: 6-15                     | 2      |
| File count: 16+                      | 3      |
| Any HIGH-risk file                   | +2     |
| Security trigger active              | +2     |
| Project type: production or library  | +1     |
| Change type: new feature or refactor | +1     |
| Change type: config or docs only     | -1     |

Clamp the final score to `max(0, score)` before depth lookup.

| Score | Depth    | Behavior                                                                 |
| ----- | -------- | ------------------------------------------------------------------------ |
| 0-3   | Light    | Inline review, 1-2 lenses, skip team structure                           |
| 4-6   | Standard | Parallel reviewers, 2+ lenses, full research validation                  |
| 7-10  | Deep     | Full team with specialists, all applicable lenses, cross-domain analysis |

Record the depth classification in the triage report. Reviewers use this to calibrate effort.

## Context Assembly

Gather project-level context that calibrates severity and informs reviewer prompts.

**Project type** -- classify to set severity bar (see SKILL.md, Review Posture):

- Prototype (no CI, few tests, single contributor): P0/S0 only
- Production (CI, test suite, multiple contributors, deploy config): full review
- Library (published package, public API, semver, changelog): full review + backward compatibility

**Architecture overview** -- record entry points, top-level dependency graph, external dependencies (DBs, APIs, queues), and layering boundaries.

**Test coverage summary:**

```bash
find [path] -name '*test*' -o -name '*spec*' | wc -l          # test files
find [path] \( -name '*.py' -o -name '*.ts' \) | grep -v test | wc -l  # source files
```

Note whether tests exist for HIGH-risk files specifically; ratio alone is insufficient.

**Recent PR history** -- check last 10 merged PRs for recurring change areas and review patterns:

```bash
gh pr list --state merged --limit 10 --json title,number,additions,deletions,changedFiles
```

## Triage Output Template

Produce this output at the end of Wave 0. Pass to all Wave 1 reviewers.

```
TRIAGE REPORT
=============
PROJECT PROFILE:
  Language(s): [primary, secondary]  |  Framework(s): [web, test, ORM]
  Build: [system]  |  Pkg mgr: [detected]
  Files: [N]  |  LOC: [N]  |  Type: [prototype | production | library]

GIT SIGNALS:
  Hot files (top 5): [path] — [N] commits (90d), [N] authors
  Recently changed (14d): [N] files
  Open issues in touched areas: [N]

RISK-SORTED FILE LIST:
  HIGH ([N] files):
    [path] — triggers: [auth, LOC>300, 5+ authors] → deep specialist review
  MEDIUM ([N] files):
    [path] — triggers: [business logic, moderate churn] → standard review
  LOW ([N] files):
    [path] — triggers: [config, LOC<50] → quick scan

SPECIALIST TRIGGERS:
  [ ] Security — auth/payments/crypto/user-data files detected
  [ ] Resilience — external I/O or distributed patterns detected
  [ ] Dependency auditor — [N]+ deps, [N] outdated
  [ ] Data migration — schema changes or migration files detected
  [ ] Backward compat — public API surface changes detected
  [ ] i18n/a11y — user-facing UI components detected

CONTEXT FOR REVIEWERS:
  Entry points: [list]
  Architecture: [brief layering description]
  Test coverage: [N] test / [N] source ([ratio])
  PR patterns: [brief summary]
```

Check each applicable specialist box. The lead uses this to determine team composition (see references/team-templates.md) and write targeted teammate prompts with the correct severity bar and checklist selection.

Cross-references: scripts/project-scanner.py, references/team-templates.md.
