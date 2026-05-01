---
status: planning
owner: platform-orchestrator
last_updated: 2026-05-01
principle: skills-first, specs-governed, mcp-when-live-state-required
---

# Skills-First Extension Policy

## Principle

Use the least powerful extension primitive that solves the problem.

## Default priority order

1. Canonical instructions and OpenSpec specs
2. Agent Skills
3. Harness-native plugins/extensions
4. MCP servers
5. Bespoke fallback adapter logic

## Why skills first

Agent Skills are portable, filesystem-based capability packages with `SKILL.md` metadata and optional scripts, references, and assets. Their progressive disclosure model lets agents load only names/descriptions initially, then full instructions/resources when relevant. The `skills` CLI can run through `npx`, and `skills.sh` provides a public discovery and lifecycle surface.

## When to use skills

Use skills for:

- codebase review playbooks
- framework conventions
- docs workflows
- security review checklists
- release workflows
- OpenSpec proposal/design/task workflows
- deterministic local scripts
- repo-specific onboarding

## When not to use skills

Do not use skills when the capability requires:

- live external state
- OAuth or remote auth flows
- browser DOM/network/runtime access
- production telemetry
- remote issue trackers
- current web/documentation retrieval

Those remain MCP/plugin candidates.

## CLI preference

Prefer:

- `npx skills ...` for skill lifecycle management
- `uvx ...` for Python MCP servers or Python CLI tools
- `npx -y ...` for Node MCP servers and Node-based CLIs

A stronger alternative may replace these defaults only if it provides better reproducibility, signatures/provenance, sandboxing, and cross-platform support.
