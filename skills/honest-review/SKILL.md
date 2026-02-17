---
name: honest-review
description: >-
  Research-driven code review and validation at multiple levels of
  abstraction. Two modes: (1) Session review — after making changes,
  review and verify work using parallel reviewers that research-validate
  every assumption; (2) Full codebase audit — deep end-to-end evaluation
  using parallel teams of subagent-spawning reviewers. Use when reviewing
  changes, verifying work quality, auditing a codebase, validating
  correctness, checking assumptions, finding defects, reducing complexity.
  NOT for writing new code, explaining code, or benchmarking.
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0"
---

# Honest Review

Research-driven code review. Every finding validated with evidence.

## Dispatch

| $ARGUMENTS | Mode |
|------------|------|
| Empty + changes in session (git diff) | Session review of changed files |
| Empty + no changes (first message) | Full codebase audit |
| File or directory path | Scoped review of that path |
| "audit" | Force full codebase audit |
| PR number/URL | Review PR changes (gh pr diff) |
| Git range (HEAD~3..HEAD) | Review changes in that range |

## Review Levels (Both Modes)

Every review covers three abstraction levels, each examining both
defects and unnecessary complexity:

**Surface** (lines, expressions, functions):
Correctness, error handling, security, readability.
Simplify: dead code, complex conditionals to early returns, hand-rolled to stdlib.

**Structural** (modules, classes, boundaries):
Test coverage, coupling, interface contracts, cognitive complexity.
Simplify: 1:1 wrappers, single-use abstractions, pass-through plumbing.

**Algorithmic** (algorithms, data structures, system design):
Complexity class, N+1, resource leaks, concurrency.
Simplify: O(n^2) to O(n), wrong data structure, unnecessary serialization.

Context-dependent: add security checks for auth/payment/user-data code.
Add observability checks for services/APIs.
Full checklists: read references/checklists.md

## Research Validation

THIS IS THE CORE DIFFERENTIATOR. Do not report findings based solely
on LLM knowledge. For every non-trivial finding, validate with research:

**Two-phase review per scope**:
1. **Flag phase**: Analyze code, generate hypotheses ("this API may be
   deprecated", "this SQL pattern may be injectable", "this dependency
   has a known CVE")
2. **Validate phase**: For each flag, spawn research subagent(s) to confirm:
   - Context7: look up current library docs for API correctness
   - WebSearch: check current best practices, security advisories
   - WebFetch: query package registries (npm, PyPI, crates.io)
   - gh: check open issues, security advisories for dependencies
3. Only report findings with evidence. Cite sources.

Research playbook: read references/research-playbook.md

## Mode 1: Session Review

### Step 1: Identify Changes

Run `git diff --name-only HEAD` to capture both staged and unstaged changes.
Collect `git diff HEAD` for full context.
Identify original task intent from session history.

### Step 2: Scale and Launch

| Scope | Strategy |
|-------|----------|
| 1-2 files | Inline review at all 3 levels. Spawn research subagents for flagged findings. |
| 3-5 files | Spawn 3 parallel reviewer subagents (Surface/Structural/Algorithmic). Each flags then researches within their level. |
| 6+ files or 3+ modules | Spawn a team. See below. |

**Team structure for large session reviews (6+ files)**:

```
[Lead: reconcile findings, produce final report]
  |-- Surface Reviewer
  |     Wave 1: subagents analyzing files (1 per file)
  |     Wave 2: subagents researching flagged findings
  |-- Structural Reviewer
  |     Wave 1: subagents analyzing module boundaries
  |     Wave 2: subagents researching flagged findings
  |-- Algorithmic Reviewer
  |     Wave 1: subagents analyzing performance/complexity
  |     Wave 2: subagents researching flagged findings
  |-- Verification Runner
        Wave 1: subagents running build, lint, tests
        Wave 2: subagents spot-checking behavior
```

Each teammate operates independently. Each runs internal waves of
massively parallelized subagents. No overlapping file ownership.

### Step 3: Reconcile (5 Steps)

1. **Question**: For each finding, ask: (a) Is this actually broken or
   just unfamiliar? (b) Is there research evidence? (c) Would fixing
   this genuinely improve the code? Discard unvalidated findings.
2. **Deduplicate**: Same issue at different levels — keep deepest root cause
3. **Resolve conflicts**: When levels disagree, choose most net simplification
4. **Elevate**: Surface patterns across files to structural/algorithmic root
5. **Prioritize**: P0/S0 (must fix), P1/S1 (should fix), P2/S2 (report but do not implement)

Severity calibration: P0 = will cause production incident. Not "ugly code."

### Step 4: Present and Execute

Present all P0/P1/S0/S1 findings with evidence and citations.
Ask: "Implement fixes? [all / select / skip]"
If approved: parallel subagents by file (no overlapping ownership).
Then verify: build/lint, tests, behavior spot-check.
Output format: read references/output-formats.md

## Mode 2: Full Codebase Audit

### Step 1: Discover

Explore: language(s), framework(s), build system, directory structure,
entry points, dependency manifest, approximate size.
For 500+ files: prioritize recently modified, entry points, public API,
high-complexity areas. State scope in report.

### Step 2: Design and Launch Team

Spawn a team with domain-based ownership. Each teammate runs all 3
review levels + research validation on their owned files.

```
[Lead: cross-domain analysis, reconciliation, final report]
  |-- Domain A Reviewer — e.g., Backend
  |     Wave 1: parallel subagents scanning all owned files
  |     Wave 2: parallel subagents deep-diving flagged files
  |     Wave 3: parallel subagents researching flagged assumptions
  |-- Domain B Reviewer — e.g., Frontend
  |     [same wave pattern]
  |-- Domain C Reviewer — e.g., Tests/Infra
  |     [same wave pattern]
  |-- Dependency and Security Researcher
        Wave 1: subagents auditing each dependency (version, CVEs, license)
        Wave 2: subagents checking security patterns against current docs
        Wave 3: subagents verifying API usage against library docs (Context7)
```

Adapt team composition to project type.
Team archetypes + scaling: read references/team-templates.md

### Step 3: Teammate Instructions

Each teammate receives: role, owned files, project context, all 3 review
levels, instruction to run two-phase (flag then research-validate), and
findings format. Full template: references/team-templates.md

### Step 4: Cross-Domain Analysis (Lead)

While teammates review, lead spawns parallel subagents for:
- Architecture: module boundaries, dependency graph
- Data flow: trace key paths end-to-end
- Error propagation: consistency across system
- Shared patterns: duplication vs. necessary abstraction

### Step 5: Reconcile Across Domains

Same 5-step reconciliation. Cross-domain deduplication and elevation.

### Step 6: Report

Output format: references/output-formats.md
Required sections: Critical, Significant, Cross-Domain, Health Summary,
Top 3 Recommendations. All findings include evidence + citations.

### Step 7: Execute (If Approved)

Ask: "Implement fixes? [all / select / skip]"
If approved: parallel subagents by file (no overlapping ownership).
Then verify: build/lint, tests, behavior spot-check.

## Healthy Codebase

If no P0/P1 or S0 findings: state this explicitly. Acknowledge health.
Do not inflate minor issues. A short report is a good report.

## Reference Files

| File | When to Read |
|------|--------------|
| references/checklists.md | During analysis or building teammate prompts |
| references/research-playbook.md | When setting up research validation subagents |
| references/output-formats.md | When producing final output |
| references/team-templates.md | When designing teams (Mode 2 or large Mode 1) |

## Critical Rules

- Every non-trivial finding must have research evidence or be discarded
- Do not police style — follow the codebase's conventions
- Do not report phantom bugs requiring impossible conditions
- More than 15 findings means re-prioritize — 5 validated findings beat 50 speculative
- Never skip reconciliation
- Always present before implementing (approval gate)
- Always verify after implementing (build, tests, behavior)
- Never assign overlapping file ownership
