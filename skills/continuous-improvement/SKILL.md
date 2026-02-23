---
name: continuous-improvement
description: >-
  Instruction file maintenance protocol. Use when a pattern is corrected 3+
  times across 2+ sessions and needs codification. Route changes to the
  correct target file. NOT for one-time fixes, skill creation, or
  project-specific rules that belong in AGENTS.md.
user-invocable: false
disable-model-invocation: false
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Continuous Improvement Protocol

Apply this protocol when considering changes to instruction files or skills.

## Dispatch

| $ARGUMENTS | Action |
|------------|--------|
| Active (auto-invoked when proposing instruction changes) | Apply routing and verification below |
| Empty | Display protocol summary |
| `route <topic>` | Determine correct target for a proposed change |

## References

| File | Purpose |
|------|---------|
| `references/routing-specifics.md` | Decision tree for where to route instruction changes |

## When to Propose Updates

Propose an instruction or skill update only when:

- A pattern is corrected **3+ times** across **2+ sessions**
- The correction is consistent (same fix each time)
- The pattern applies broadly, not to a single project

Do NOT propose changes for:

- One-time fixes or edge cases
- Personal preferences without repeated evidence
- Rules that contradict existing higher-priority instructions

## Routing

Route proposed updates to the correct target:

| Scope | Target | Example |
|-------|--------|---------|
| Cross-project conventions | `instructions/global.md` | Orchestration patterns, general coding style |
| Language-specific tooling | Corresponding language skill | "Use uv" goes to python-conventions |
| Orchestration/parallelism | `orchestrator` skill body | Team patterns, wave dispatch |
| Project-specific standards | Project's `AGENTS.md` | Repo-specific naming, workflows |
| Skill behavior | The skill's own `SKILL.md` | Fixing a skill's instructions |

### Routing Decision Steps

1. Determine the scope: does this apply to all projects or just one?
2. If cross-project, does it relate to a specific language or tool?
3. If language-specific, route to the corresponding convention skill
4. If general, route to `instructions/global.md`
5. If project-only, route to the project's `AGENTS.md`

## Verification Checklist

Before proposing any instruction change:

1. **Verify against actual practice** -- confirm the pattern reflects real usage, not a one-off preference
2. **Check for contradictions** -- ensure the change does not conflict with existing instructions
3. **Assess token impact** -- keep always-loaded content minimal (see token budget in AGENTS.md)
4. **Get user approval** -- never modify instruction files without explicit user consent
5. **Test the change** -- run `wagents validate` after any instruction file edit

## Critical Rules

1. Never modify instruction files without explicit user approval
2. Require 3+ corrections across 2+ sessions before proposing a change
3. Always check for contradictions with existing instructions before proposing
4. Route changes to the narrowest applicable scope (skill before global)
5. Keep always-loaded instruction content under the token budget
6. Verify proposed changes against actual practice, not theoretical ideals
7. Run `wagents validate` after every instruction file modification

**Canonical terms** (use these exactly):
- `instruction file` -- any file that provides agent instructions (global.md, AGENTS.md, SKILL.md)
- `routing` -- the process of choosing the correct target file for a change
- `correction pattern` -- a repeated fix that indicates a missing or wrong instruction
- `token budget` -- the limit on always-loaded instruction content
- `scope` -- cross-project, language-specific, orchestration, or project-specific
