# Dispatch Pack

This directory contains child-agent execution prompts for the agents platform overhaul.

## Global Rules

- Parent OpenSpec change: `agents-platform-overhaul`.
- Child agents must edit only their allowed paths.
- Child agents must not edit `README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, parent tasks, or generated support matrices directly.
- Use fragments, manifests, fixtures, and child OpenSpec artifacts; regenerate global docs later.
- Do not install external repositories by default.
- Prefer Agent Skills for deterministic portable capabilities.
- Use MCP only for live external state and dynamic runtime capabilities.
- Commit each completed child lane as a logical unit once validation passes.

## Waves

| Wave | Dispatches |
|---|---|
| 0 | `agents-c00-repo-sync`, `agents-c01-registry-core`, `agents-c10-external-repo-intake`, `agents-c08-docs-instructions` |
| 1 | `agents-c02-skills-lifecycle`, `agents-c03-mcp-audit`, `agents-c04-*`, `agents-c11-knowledge-graph-context`, `agents-c12-session-telemetry`, `agents-c13-skill-registry-intake`, `agents-c15-security-quarantine` |
| 2 | `agents-c05-ux-cli`, `agents-c06-config-safety`, `agents-c07-ci-evals-observability`, `agents-c14-multiagent-ui-patterns` |
| 3 | `agents-c09-release-archive` |
