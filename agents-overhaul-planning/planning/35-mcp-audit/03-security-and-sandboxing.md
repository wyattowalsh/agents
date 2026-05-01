# MCP Security and Sandboxing

## Source-backed risk classes

MCP security tooling and research identifies risks including:

- prompt injection in tool descriptions;
- tool poisoning;
- rug pulls/tool changes after install;
- cross-origin escalation/tool shadowing;
- toxic flows between tools;
- excessive filesystem/network privileges;
- credential exposure through environment variables.

Source: https://explorer.invariantlabs.ai/docs/mcp-scan/

## Required controls

| Control | Requirement |
|---|---|
| Static scan | Run `uvx mcp-scan@latest` or `npx mcp-scan@latest` against configured MCP files |
| Tool pinning | Hash tool descriptions where feasible |
| Config lint | Reject absolute local paths in validated profiles |
| Secret policy | Env vars must be named and documented; no secrets in args/logs |
| Transport policy | stdio preferred for local; Streamable HTTP requires origin validation/auth review |
| Scope policy | Read-only first; write actions need explicit support-tier escalation |
| Human docs | Setup docs must explain permissions and rollback |

## CI gates

- `mcp-registry.schema` validation.
- MCP scan report attached as artifact.
- Install command dry-run where possible.
- Tool list snapshot diff.
- Secret reference check.
- Replacement-by-skill check.
