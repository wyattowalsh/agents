---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# CI/CD and Conformance Plan

## Goal

Make generated artifacts, harness configs, skills, MCPs, docs, and OpenSpec state continuously verifiable.

## Proposed CI jobs

1. `schema-validate`
2. `skills-validate`
3. `registry-validate`
4. `adapter-golden-fixtures`
5. `clean-room-install`
6. `mcp-smoke-tests`
7. `openspec-validate`
8. `docs-generate-check`
9. `security-scan`
10. `release-bundle-check`

## Blocking gates

- schema validation
- stale generated docs
- invalid skills
- unsafe secrets in config
- first-class harness fixture failure
- OpenSpec task/spec mismatch for active change
