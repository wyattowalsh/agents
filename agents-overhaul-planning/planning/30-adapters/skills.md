---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Skills Adapter

## Goal

Project canonical skills into harness-compatible locations without losing portability.

## Preferred target

Use `.agents/skills/<name>/SKILL.md` as the canonical repo-local project skill location when a harness supports it. Use harness-specific mirrors only when required.

## Conformance

- validate `SKILL.md` frontmatter
- ensure names match directory names
- run script lint/audit for executable files
- verify generated install commands
