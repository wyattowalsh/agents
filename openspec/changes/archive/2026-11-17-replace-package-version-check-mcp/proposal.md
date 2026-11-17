# Proposal: Replace package-version with package-version-check-mcp

## Problem

The managed MCP registry launches legacy Go `mcp-package-version` with six `check_*` tools. Upstream [MShekow/package-version-check-mcp](https://github.com/MShekow/package-version-check-mcp) provides broader ecosystem coverage, maintained tests, and PyPI `uvx` distribution.

## Intent

Replace the server with `package-version-check-mcp` (PyPI 1.2.20, Apache-2.0, audit 2026-07-04), rename MCPHub slug, refresh groups (`harness`, `tunnel`, workflow bundles, `research`), and update downstream harness projections, skills, and docs.

## Scope

- Registry server swap via `scripts/mcphub/package-version-check-mcp.sh` (patches upstream PyPI 1.2.x `version_parser.py`, then `uvx --mode=stdio`)
- Optional env: `GITHUB_PAT` for GitHub Actions rate limits
- Groups: `harness` (default bounded / former harness-safe), `tunnel`, `daily`, `coding`, `review`, `release`, `repo`, `shared-read`, plus new `research` membership
- Breaking endpoint: `/mcp/package-version` → `/mcp/package-version-check-mcp`

## Out of scope

- Vendoring server under `mcp/`
- Hosted Render HTTP mode
- Home sync unless user requests
- Recreating deprecated `harness-safe` group name (`harness` is the live successor)

## Affected surfaces

- `config/mcp-registry.json`, `mcp/mcphub/mcp_settings.json`
- Harness projections via `scripts/sync_agent_stack.py`
- `skills/research/*`, `skills/mcphub-operator/references/group-picker.md`
- Docs: `mcp-registry.mdx`, `mcp/index.mdx`, generated research catalog