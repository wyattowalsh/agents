# Claude Plugin Package Plan

## Source facts

Claude Code plugins can bundle commands, agents, hooks, Skills, MCP servers, LSP servers, and monitors. Plugin marketplaces are JSON catalogs for discovery and version management.

Sources:

- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/plugins-reference
- https://code.claude.com/docs/en/plugin-marketplaces

## Repo application

The repo already has `.claude-plugin/`. The plan should:

- inventory existing plugin manifest;
- generate manifest sections from canonical registry;
- package only validated skills by default;
- allow experimental MCPs only behind explicit profile flags;
- add plugin manifest fixture tests;
- document marketplace install/update behavior.
