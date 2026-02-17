# Team Templates

Team archetypes, scaling guidance, and prompt templates.
Read when designing review teams (Mode 2 or large Mode 1).

## Session Review Team (6+ Files)

```
[Lead: reconcile, final report]
  |-- Surface Reviewer (owns: all changed files, surface-level analysis)
  |-- Structural Reviewer (owns: module boundaries, cross-file patterns)
  |-- Algorithmic Reviewer (owns: performance, complexity, system design)
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
> - **Surface**: correctness, error handling, security, readability, simplification
> - **Structural**: test coverage, coupling, interface contracts, simplification
> - **Algorithmic**: performance, resource usage, concurrency, simplification
>
> Use two-phase review:
> 1. Flag: analyze code, generate hypotheses about defects and complexity
> 2. Validate: spawn parallel research subagents to confirm each flag using Context7 (library docs), WebSearch (best practices, advisories), WebFetch (package registries), gh (issues, advisories)
>
> Also check: technical debt (TODOs, deprecated usage), dependency health, consistency (naming, error handling, logging patterns).
>
> Return findings grouped by file with priority (P0-P2 defects, S0-S2 simplifications). Each finding must include evidence and citation. Discard findings with no research evidence.

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
> Return findings with priority, evidence, and citation. Discard findings with no research evidence.
