---
name: agent-conventions
description: >-
  Agent definition conventions. When creating or modifying agents at any level
  (~/.claude/agents/, .claude/agents/, or project-local), always update the
  corresponding README.md index with the new entry (table row + description section).
user-invocable: false
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# Agent Conventions

Apply these conventions when creating or modifying AI agent definitions.

## README Index Requirement

When defining a new agent at **any** level:

- `~/.claude/agents/`
- `.claude/agents/` (project-level)
- Project-local agent directories

You **must** update the corresponding `README.md` index in the same directory:

1. Add a row to the index table with the agent name, description, and key fields
2. Add a description section with usage details

This keeps agent directories self-documenting and discoverable.
