# Proposal

## Problem

Local MCP configuration is currently projected directly into each AI client. That
duplicates process ownership, auth behavior, observability, grouping, and
OpenAPI export across clients. Adding or removing a server requires each client
surface to be correct at the same time.

## Intent

Introduce MCPHub as the preferred local MCP control plane. The repo registry
remains the source of truth for server definitions, while MCPHub owns local MCP
server processes, groups, bearer-auth routing, logs, OpenAPI export, optional
Smart Routing, and client endpoint projection.

## Scope

- Add MCPHub registry metadata, generated `mcp_settings.json`, and local launch
  automation.
- Render MCPHub all/group/server endpoints into supported local clients when
  `mcphub.enabled` is true.
- Preserve direct per-server rendering for registries that omit `mcphub`.
- Add docs for first run, local secrets, admin login/token flow, endpoint
  taxonomy, OpenAPI export, Smart Routing opt-in, wrappers, LaunchAgent, and
  troubleshooting.
- Add validation for group references, routing requirements, and tracked
  secret-looking literals.

## Out Of Scope

- Docker-based MCPHub startup.
- Public network exposure.
- Committing local admin passwords, JWT secrets, bearer tokens, database
  passwords, OAuth secrets, or provider API keys.
- Enabling Smart Routing by default.
- Claiming live sync support for clients with no verified local MCP config
  surface.

## Risks

- OpenAPI endpoints are documented as public by MCPHub, so the local service
  must remain bound to localhost.
- Personal-account groups expose sensitive tools through the hub and should be
  targeted deliberately.
- Smart Routing requires PostgreSQL pgvector and embeddings; enabling it without
  those dependencies will fail or degrade tool discovery.
