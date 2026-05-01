# MCP Secondary Adapter

## Objective

Project curated MCP servers into harness-specific MCP config only when a live-systems justification exists.

## Responsibilities

- Resolve MCP package/install command.
- Pin versions where feasible.
- Encode transport and auth model.
- Emit environment variable requirements without secrets.
- Add sandbox constraints.
- Generate smoke tests.
- Run security scans such as mcp-scan where possible.
- Generate deprecation and rollback metadata.

## Default policy

- Prefer `uvx` for Python MCP servers where upstream supports it.
- Prefer `npx` for Node MCP servers where upstream supports it.
- Avoid long-lived global installs unless required.
- Avoid filesystem/git MCPs when native harness tools or skill/CLI wrappers suffice.
