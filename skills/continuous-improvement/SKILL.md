---
name: continuous-improvement
description: >-
  Instruction file maintenance protocol. Propose updates when a pattern is corrected
  3+ times across 2+ sessions. Route: cross-project → global.md, language-specific →
  language skill, orchestration → orchestrator skill, project → AGENTS.md.
  Verify against actual practice, check for contradictions, get user approval.
user-invocable: false
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Continuous Improvement Protocol

Apply this protocol when considering changes to instruction files or skills.

## When to Propose Updates

Propose an instruction or skill update when a pattern is corrected **3+ times** across **2+ sessions**.

## Routing

Route proposed updates to the correct target:

| Scope | Target |
|-------|--------|
| Cross-project conventions | `instructions/global.md` |
| Language-specific tooling | Corresponding language conventions skill |
| Orchestration/parallelism | `orchestrator` skill or orchestration core in global.md |
| Project-specific standards | Project's `AGENTS.md` |

## Verification Checklist

Before proposing any instruction change:

1. **Verify against actual practice** — confirm the pattern reflects real usage, not a one-off preference
2. **Check for contradictions** — ensure the change doesn't conflict with existing instructions
3. **Get user approval** — never modify instruction files without explicit user consent
