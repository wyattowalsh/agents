# Design

## Approach

Mirror the jupyter-mcp-server integration pattern:

1. Machine-local sparse checkout of upstream `.claude/skills` at release **21.1.0**.
2. `npm install && npm run build` → `dist/mcp-server.js`.
3. Repo wrapper `scripts/mcphub/qsv-stdio.sh` resolves `qsvmcp` or `qsv`, sets env, execs node.
4. Registry entry with `tools: ["*"]` and explicit `tools_allow_all: true`.
5. New capability group `data` (primary); also attach full server to `coding` and `research`.
6. Curated-external skill catalog (15 skills) for Skills CLI sync across harnesses.

## Group Membership

| Group | Shape |
|-------|-------|
| `data` (NEW) | full server — primary home |
| `coding` | full server |
| `research` | full server |
| `harness`, `tunnel` | excluded |

## Env / Allowlist

| Variable | Default |
|----------|---------|
| `QSV_MCP_BIN_PATH` | auto: `qsvmcp` then `qsv` |
| `QSV_MCP_WORKING_DIR` | `${REPO_ROOT}` |
| `QSV_MCP_ALLOWED_DIRS` | `${REPO_ROOT}:${HOME}/dev` (plan lock) |
| `QSV_MCP_CHECK_UPDATES_ON_STARTUP` | `false` |

Upstream still denylists sensitive home dirs (`.ssh`, `.aws`, `.kube`, …).

## Capability mapper bypass

Manual maintainer mapping is sufficient: single server, known tool set (~23 deferred tools), explicit group topology locked by plan. Verified by registry pytest + membership assert + docs update. Follow-up: optional `mcp-capability-mapper` pass if tool inventory grows.

## Alternatives Rejected

- npm package install: `@qsv/agent-skills` not published (404).
- Default `harness` membership: deferred tool tax violates bounded harness policy.
- Skills without MCP: skill bodies hard-require `mcp__qsv__*` tools.
- New group only without coding/research: reduces discoverability during coding/research workflows.

## Migration

No compatibility shim. Additive registry + catalog only.
