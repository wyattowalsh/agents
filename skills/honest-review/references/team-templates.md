# Team Templates

Team archetypes, scaling guidance, and prompt templates.
Read when designing review teams (Mode 2 or large Mode 1).

## Contents

- [Session Review Team](#session-review-team-6-files)
- [Full Audit Team Archetypes](#full-audit-team-archetypes)
- [Scaling Matrix](#scaling-matrix)
- [Teammate Prompt Template (Full Audit)](#teammate-prompt-template-full-audit)
- [Mode 1 Reviewer Prompt Template](#mode-1-reviewer-prompt-template)

## Session Review Team (6+ Files)

```
[Lead: reconcile, final report]
  |-- Correctness Reviewer (owns: all changed files, correctness-level analysis)
  |-- Design Reviewer (owns: module boundaries, cross-file patterns)
  |-- Efficiency Reviewer (owns: performance, complexity, system design)
  |-- Verification Runner (owns: build, tests, behavior checks)
```

Each reviewer runs Wave 1 (analysis subagents) then Wave 2 (research subagents).

## Full Audit Team Archetypes

### Web Application

```
[Lead: cross-domain analysis, reconciliation, final report]
  |-- Backend Reviewer (owns: src/api/, src/db/, src/services/)
  |-- Frontend Reviewer (owns: src/components/, src/styles/, src/pages/)
  |-- Tests/Config Reviewer (owns: tests/, CI/CD, configs, build scripts)
  |-- Dependency and Security Researcher (owns: dependency audit, security patterns)
```

### Library/SDK

```
[Lead: cross-domain analysis, reconciliation, final report]
  |-- Core Reviewer (owns: src/core/, src/lib/)
  |-- API Surface Reviewer (owns: public API, types, exports)
  |-- Tests/Docs Reviewer (owns: tests/, benchmarks/, docs/)
  |-- Dependency and Security Researcher (owns: dependency audit, security patterns)
```

### Monorepo

```
[Lead: cross-domain analysis, reconciliation, final report]
  |-- Package A Reviewer (owns: packages/a/)
  |-- Package B Reviewer (owns: packages/b/)
  |-- Shared/Infra Reviewer (owns: packages/shared/, root configs, CI/CD)
  |-- Dependency and Security Researcher (owns: dependency audit, security patterns)
```

### CLI Tool

```
[Lead: cross-domain analysis, reconciliation, final report]
  |-- Core Commands Reviewer (owns: src/commands/, src/core/)
  |-- I/O and Config Reviewer (owns: src/io/, src/config/, config files)
  |-- Tests Reviewer (owns: tests/)
  |-- Dependency and Security Researcher (owns: dependency audit, security patterns)
```

### Data Pipeline

```
[Lead: cross-domain analysis, reconciliation, final report]
  |-- Ingestion Reviewer (owns: src/ingest/, src/sources/)
  |-- Transform Reviewer (owns: src/transform/, src/models/)
  |-- Output/Infra Reviewer (owns: src/output/, src/infra/, configs)
  |-- Dependency and Security Researcher (owns: dependency audit, security patterns)
```

## Scaling Matrix

| Files | Teammates | Notes |
|-------|-----------|-------|
| Under 20 | 2-3 | Merge test into domain reviewer; 1 dep researcher |
| 20-100 | 3-4 | Standard archetypes above |
| 100-500 | 4-5 | Split large domains into sub-domains |
| 500+ | 5-6 | Multiple passes, state scope limits in report |

## Teammate Prompt Template (Full Audit)

Use this template when spawning domain reviewers:

> You are the **[Domain] Reviewer** in a full codebase audit.
>
> **Your owned files:** [directory/glob patterns]
> **Project context:** [language, framework, build system, entry points]
>
> Conduct a deep review of every file in your ownership. Spawn parallel subagents to cover files concurrently.
>
> For each file, run all three analysis levels:
> - **Correctness**: correctness, error handling, security, readability, simplification
> - **Design**: test coverage, coupling, interface contracts, simplification
> - **Efficiency**: performance, resource usage, concurrency, simplification
>
> Use two-phase review:
> 1. Flag: analyze code, generate hypotheses about defects and complexity
> 2. Validate: spawn parallel research subagents to confirm each flag using Context7 (library docs), WebSearch (best practices, advisories), WebFetch (package registries), gh (issues, advisories)
>
> Also check: technical debt (TODOs, deprecated usage), dependency health, consistency (naming, error handling, logging patterns).
>
> Apply at least 2 creative review lenses from references/review-lenses.md (pick based on code characteristics: Inversion for assumption-heavy code, Deletion for mature codebases, Newcomer for complex modules, Incident for production services, Evolution for growing systems).
>
> Check for AI code smells: slopsquatting (verify every import exists in the package registry), hallucinated APIs, sycophantic comments, phantom error handling, over-engineering disproportionate to problem size.
>
> For each finding, include effort estimation: S (< 1 hour, single file), M (1-4 hours, few files), L (4+ hours, cross-cutting).
>
> Include a STRENGTHS section: identify at least one well-engineered pattern or positive design choice per owned domain.
>
> Return findings grouped by file with priority (P0-P2 defects, S0-S2 simplifications). Each finding must include evidence, citation, and effort estimate. Discard findings with no research evidence.

## Mode 1 Reviewer Prompt Template

Use this template when spawning level-specific reviewers for session review:

> You are the **[Level] Reviewer** for a session review.
>
> **Changed files:** [list of files with change type]
> **Task intent:** [what the session was trying to accomplish]
>
> Review all changed files at the **[level]** level using the checklist from references/checklists.md.
>
> Use two-phase review:
> 1. Flag: analyze code for defects and unnecessary complexity
> 2. Validate: spawn parallel research subagents for non-obvious findings
>
> Apply at least 2 creative review lenses (pick from: Inversion, Deletion, Newcomer, Incident, Evolution — see references/review-lenses.md).
>
> Check for AI code smells if code appears LLM-generated: slopsquatting, hallucinated APIs, sycophantic comments, phantom error handling.
>
> Include a STRENGTHS section with at least one positive finding. Include effort estimation (S/M/L) per finding.
>
> Return findings with priority, evidence, citation, and effort estimate. Discard findings with no research evidence.
