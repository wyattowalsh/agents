# Team Templates

Team archetypes, specialist agents, scaling guidance, and prompt templates.
Read when designing review teams (Mode 2 or large Mode 1).

## Contents

- [Session Review Team](#session-review-team-6-files)
- [Specialist Agents](#specialist-agents)
- [Full Audit Team Archetypes](#full-audit-team-archetypes)
- [Scaling Matrix](#scaling-matrix)
- [Internal Pass Structure](#internal-pass-structure)
- [Teammate Prompt Template (Full Audit)](#teammate-prompt-template-full-audit)
- [Mode 1 Reviewer Prompt Template](#mode-1-reviewer-prompt-template)
- [Specialist Prompt Templates](#specialist-prompt-templates)

## Session Review Team (6+ Files)

```
[Lead: triage, reconcile (Judge protocol), final report]
  |-- Correctness Reviewer (all files, correctness-level focus)
  |-- Design Reviewer (all files, design-level focus)
  |-- Efficiency Reviewer (all files, efficiency-level focus)
  |-- [Context-triggered specialists — see below]
```

For 3-5 files: spawn 3 level-based reviewers (no lead team, lead reconciles directly).
For 6+ files: full team with lead orchestration.
For 6+ files spanning 3+ modules: consider switching to domain-based ownership (Full Audit archetypes) instead.

## Specialist Agents

Context-triggered agents that run cross-cutting analysis across all domains. Activate based on triage results (see references/triage-protocol.md, Specialist Triggers section).

**Security Specialist** — activate when triage detects auth, payments, crypto, user-data, or file I/O files.

- Runs Adversary lens (mandatory) across all HIGH-risk files
- Cross-references OWASP Top 10, checks auth boundaries, injection vectors, supply chain
- Uses: WebSearch (OWASP, CVE databases), Context7 (library security docs), WebFetch (package registries)

**Observability Specialist** — activate for production services with external dependencies.

- Checks structured logging, RED metrics, distributed tracing, health checks, silent failures
- Applies Incident lens across service entry points
- Uses: Context7 (framework observability docs), WebSearch (best practices)

**Requirements Validator** — activate when PR description, linked issues, or stated intent is available.

- Validates implementation matches stated intent, edge cases handled, acceptance criteria met
- Checks for silently dropped requirements and scope creep
- Uses: gh (issue details, PR description), session history

## Full Audit Team Archetypes

### Web Application

```
[Lead: triage, cross-domain analysis, Judge reconciliation, final report]
  |-- Backend Reviewer (owns: src/api/, src/db/, src/services/)
  |-- Frontend Reviewer (owns: src/components/, src/styles/, src/pages/)
  |-- Tests/Config Reviewer (owns: tests/, CI/CD, configs, build scripts)
  |-- Security Specialist (cross-cutting, all HIGH-risk files)
  |-- [Observability Specialist if production service]
```

### Library/SDK

```
[Lead: triage, cross-domain analysis, Judge reconciliation, final report]
  |-- Core Reviewer (owns: src/core/, src/lib/)
  |-- API Surface Reviewer (owns: public API, types, exports)
  |-- Tests/Docs Reviewer (owns: tests/, benchmarks/, docs/)
  |-- Security Specialist (cross-cutting)
  |-- [Requirements Validator if semver/changelog changes]
```

### Monorepo

```
[Lead: triage, cross-domain analysis, Judge reconciliation, final report]
  |-- Package A Reviewer (owns: packages/a/)
  |-- Package B Reviewer (owns: packages/b/)
  |-- Shared/Infra Reviewer (owns: packages/shared/, root configs, CI/CD)
  |-- Security Specialist (cross-cutting)
```

### CLI Tool

```
[Lead: triage, cross-domain analysis, Judge reconciliation, final report]
  |-- Core Commands Reviewer (owns: src/commands/, src/core/)
  |-- I/O and Config Reviewer (owns: src/io/, src/config/, config files)
  |-- Tests Reviewer (owns: tests/)
  |-- Security Specialist (cross-cutting, especially command injection vectors)
```

### Data Pipeline

```
[Lead: triage, cross-domain analysis, Judge reconciliation, final report]
  |-- Ingestion Reviewer (owns: src/ingest/, src/sources/)
  |-- Transform Reviewer (owns: src/transform/, src/models/)
  |-- Output/Infra Reviewer (owns: src/output/, src/infra/, configs)
  |-- Security Specialist (cross-cutting)
  |-- [Observability Specialist for production pipelines]
```

### Mobile App

```text
[Lead: triage, cross-domain analysis, Judge reconciliation, final report]
  |-- UI/Presentation Reviewer (owns: views/, screens/, components/, storyboards)
  |-- Logic/Services Reviewer (owns: services/, models/, viewmodels/, state management)
  |-- Platform/Native Reviewer (owns: native modules, platform configs, permissions)
  |-- Security Specialist (cross-cutting, especially data at rest, keychain, biometrics)
```

### AI/ML Pipeline

```text
[Lead: triage, cross-domain analysis, Judge reconciliation, final report]
  |-- Model/Training Reviewer (owns: models/, training/, fine-tuning scripts)
  |-- Data Processing Reviewer (owns: data/, preprocessing/, feature engineering)
  |-- Inference/Serving Reviewer (owns: inference/, serving/, API endpoints)
  |-- Security Specialist (cross-cutting, especially model poisoning, prompt injection)
  |-- [Observability Specialist for production inference services]
```

### Plugin/Extension

```text
[Lead: triage, cross-domain analysis, Judge reconciliation, final report]
  |-- Core Logic Reviewer (owns: src/, handlers/, commands/)
  |-- Integration/Host API Reviewer (owns: extension API usage, manifest, permissions)
  |-- Tests/Config Reviewer (owns: tests/, build configs, packaging)
  |-- Security Specialist (cross-cutting, especially host API permissions, data exfiltration)
```

## Scaling Matrix

| Files    | Teammates | Subagents per Teammate | Notes                                |
| -------- | --------- | ---------------------- | ------------------------------------ |
| Under 20 | 2-3       | 3-5 per wave           | Merge test into domain reviewer      |
| 20-100   | 3-4       | 5-8 per wave           | Standard archetypes above            |
| 100-500  | 4-5       | 5-8 per wave           | Split large domains into sub-domains |
| 500+     | 5-6       | 5-8 per wave           | Multiple passes, state scope limits  |

**Diminishing returns:** More than 6 parallel reviewers per wave shows diminishing quality. Prefer deeper per-reviewer analysis over wider fan-out.

**Batch sizing:**

| Phase                        | Optimal Batch             | Upper Bound                    |
| ---------------------------- | ------------------------- | ------------------------------ |
| File analysis (Pass A/B)     | 3-5 files per subagent    | 8 files (quality degrades)     |
| Research validation (Pass C) | 5-8 findings per subagent | 10 findings (quality degrades) |

## Internal Pass Structure

Each domain teammate runs 3 internal passes of parallel subagents:

```
Pass A: Quick Scan (haiku subagents, 1 per chunk of 3-5 files)
  → For each file: check all 3 levels, flag potential issues
  → Output: list of flagged files with preliminary findings

Pass B: Deep Dive (opus subagents, 1 per HIGH-risk flagged file)
  → Full analysis of flagged files with creative lenses
  → Output: detailed findings with evidence hypotheses

Pass C: Research Validate (mixed models, batched by validation type)
  → Group findings by type, dispatch per references/research-playbook.md
  → Assign confidence scores per the Confidence Scoring Rubric
  → Output: validated findings with confidence scores and citations
```

Teammates report findings with: finding ID (HR-{S|A}-{seq}), priority, confidence score, evidence, citation, effort estimate.

## Teammate Prompt Template (Full Audit)

Use this template when spawning domain reviewers. Inject triage context from Wave 0.

> You are the **[Domain] Reviewer** in a full codebase audit.
>
> **Your owned files:** [directory/glob patterns]
> **Project context:** [language, framework, build system, entry points]
> **Triage context:** [paste relevant sections from Wave 0 triage report — risk classifications, hot files, specialist triggers]
>
> Conduct a deep review of every file in your ownership using 3 internal passes:
>
> **Pass A — Quick Scan:** Spawn parallel haiku subagents (1 per chunk of 3-5 files). Each scans all three levels:
>
> - Correctness: error handling, security, boundary conditions, resource leaks
> - Design: coupling, test coverage, interface contracts, cognitive complexity
> - Efficiency: algorithmic complexity, N+1, data structure choice, resource usage
>   Flag files needing deep analysis. Skip LOW-risk files with no flags.
>
> **Pass B — Deep Dive:** Spawn parallel opus subagents (1 per HIGH-risk flagged file). Full analysis with at least 2 creative lenses (references/review-lenses.md). Check context-dependent items from references/checklists.md. For security-sensitive code, Adversary lens is mandatory.
>
> **Pass C — Research Validate:** Collect all findings from Passes A and B. Group by validation type and dispatch per references/research-playbook.md. Assign confidence scores (0.0-1.0) using the Confidence Scoring Rubric.
>
> Also check: AI code smells (slopsquatting, hallucinated APIs, model-specific patterns, test-implementation mismatch).
>
> For each finding, include: finding ID (HR-A-{seq}), priority (P0-P2/S0-S2), level, confidence score, evidence with citation, effort estimate (S/M/L).
>
> Include a STRENGTHS section: at least one well-engineered pattern per owned domain.
>
> Return findings grouped by file. Discard findings with confidence < 0.3 (except P0/S0 — report those as unconfirmed).

## Mode 1 Reviewer Prompt Template

Use this template when spawning level-specific reviewers for session review.

> You are the **[Level] Reviewer** for a session review.
>
> **Changed files:** [list of files with change type and risk level from triage]
> **Task intent:** [what the session was trying to accomplish]
> **Triage context:** [risk classifications, hot files from Wave 0]
>
> Review all changed files at the **[level]** level using references/checklists.md.
>
> Run 3 internal passes:
>
> - **Pass A:** Quick scan all files (haiku subagents, 1 per 3-5 file chunk)
> - **Pass B:** Deep dive HIGH-risk flagged files (opus subagents, 1 per file)
> - **Pass C:** Research validate findings (batched per references/research-playbook.md)
>
> Apply at least 2 creative lenses (see references/review-lenses.md). For security-sensitive code, Adversary lens is mandatory.
>
> Check for AI code smells if code appears LLM-generated: slopsquatting, hallucinated APIs, model-specific patterns, test-implementation mismatch.
>
> Assign finding IDs (HR-S-{seq}), confidence scores (0.0-1.0), and effort estimates (S/M/L).
>
> Include a STRENGTHS section with at least one positive finding.
>
> Return findings with priority, confidence, evidence, citation, and effort. Discard findings with confidence < 0.3 (except P0/S0).

## Specialist Prompt Templates

### Security Specialist

> You are the **Security Specialist** performing cross-cutting security analysis.
>
> **HIGH-risk files:** [list from triage — auth, payments, crypto, user-data, file I/O]
> **All changed files:** [full list for supply chain context]
> **Triage context:** [risk classifications, dependency info]
>
> Apply the Adversary lens (mandatory) to all HIGH-risk files:
>
> 1. Enumerate attacker goals for each file's domain
> 2. Map attack surfaces and trust boundary crossings
> 3. Trace exploitation paths per OWASP Top 10
>
> Also run: slopsquatting detection (PRIORITY — WebFetch all unfamiliar dependencies), supply chain audit (unpinned versions, missing lockfile integrity), auth boundary check, injection vector scan.
>
> Research-validate every finding against current OWASP guidance and library security docs.
> Assign confidence scores. Finding IDs: HR-{S|A}-{seq}.

### Observability Specialist

> You are the **Observability Specialist** reviewing production readiness.
>
> **Service entry points:** [list from triage]
> **External dependencies:** [list from triage]
>
> Apply the Incident lens: trace failure modes for each external dependency. Check: structured logging (levels, context, no PII), RED metrics instrumentation, distributed tracing propagation, health check completeness, silent failure detection.
>
> Research-validate observability patterns against framework-specific docs via Context7.
> Assign confidence scores. Finding IDs: HR-{S|A}-{seq}.

Cross-references: references/triage-protocol.md (risk classification, specialist triggers), references/judge-protocol.md (reconciliation of findings across reviewers), references/research-playbook.md (confidence scoring, batch routing), references/output-formats.md (finding format, report structure).
