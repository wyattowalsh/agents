# Affected Surfaces

## Owned

- `planning/35-mcp-audit/`
- `planning/manifests/` for future MCP-specific audit manifests only
- `openspec/changes/agents-c03-mcp-audit/`
- MCP smoke fixtures when explicitly scheduled

## Read-Only Inputs

- `config/mcp-registry.json`
- `config/schemas/mcp-registry.schema.json`
- `planning/manifests/mcp-conformance-requirements.json`
- Project `mcp.json` shape, without editing it in this pass

## Out Of Scope

- Root `README.md` and `AGENTS.md`
- `skills/`
- Live user config outside the repo
- Secret file contents under local MCP checkouts or credential paths
