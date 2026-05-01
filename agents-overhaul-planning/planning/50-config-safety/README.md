---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Config Safety Overview

## Goal

Make multi-harness config updates safe, reversible, transparent, and secret-safe.

## Required transaction model

1. detect current config
2. parse and normalize
3. render desired state
4. compute diff
5. present preview
6. create backup snapshot
7. apply atomic write
8. validate read-back
9. run harness-specific smoke check
10. rollback on failure

## No-go rules

- Do not write inline secrets.
- Do not overwrite unknown user config without merge/diff.
- Do not mutate global config unless user asked for global scope.
- Do not enable experimental MCPs by default.
