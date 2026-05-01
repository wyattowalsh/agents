# Executive Outline

## Objective

Refactor the agents repository into a governed, skills-first, multi-harness agent infrastructure system that can install, validate, sync, audit, and document agent capabilities across Claude, ChatGPT, Codex, GitHub Copilot, OpenCode, Gemini, Cursor, Cherry Studio, Perplexity, Antigravity, and adjacent tools.

## Primary design decision

Prefer **Agent Skills** for reusable, portable, CLI-friendly capabilities. Use **MCP** only when the capability requires dynamic external state, long-lived remote APIs, browser/runtime control, authenticated SaaS access, or live telemetry/research.

## Proposed top-level changes

1. Convert all reusable capabilities into spec-conformant skill packages where feasible.
2. Introduce a canonical harness registry and generated support matrices.
3. Add a canonical external capability catalog for skills, plugins, MCPs, and harness-native extensions.
4. Add transaction-safe config sync with preview/diff/backup/apply/validate/rollback.
5. Add skill lifecycle commands: detect, install, pin, verify, update, rollback, and audit.
6. Add MCP lifecycle commands: inspect, classify, smoke-test, sandbox, pin, and deprecate.
7. Add OpenSpec-governed change management for all P0/P1 architectural work.
8. Add generated docs and AI instructions as first-class build artifacts.
9. Add conformance tests for every supported harness projection.
10. Add UI/UX flows for one-command bootstrap, skill catalog browsing, drift detection, guided remediation, and dashboard views.

## Execution model

The work is decomposed into parallel clusters:

- Repo Sync and OpenSpec Reconciliation
- Canonical Registry Core
- Skills-First Packaging and Lifecycle
- MCP Curation and Live-Systems Layer
- Harness-Specific Projections
- CLI/UI Automation
- Config Safety and Supply Chain
- CI/CD, Evals, and Observability
- Docs and AI Instructions
- Migration and Release

## Definition of success

The repo is successful when:

- A new contributor can run a single doctor command and understand what is installed, missing, stale, unsafe, or unsupported.
- A harness projection can be generated, previewed, applied, validated, and rolled back.
- Skills are packaged according to a portable spec and tested for CLI determinism.
- MCP servers are curated only when they provide live-state value not better delivered by a skill.
- README, docs, AI instructions, support matrices, and OpenSpec tasks are generated or checked against a single source of truth.
