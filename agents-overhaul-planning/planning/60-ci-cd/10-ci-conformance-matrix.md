# CI Conformance Matrix

## Gate matrix

| Gate | Applies to | Command target | Blocking |
|---|---|---|---|
| Repo inventory | all PRs touching planning or source | `wagents inventory --check` | Yes |
| Skill spec validation | `skills/**` | `wagents skills validate` | Yes |
| Skill script contract | `skills/**/scripts/**` | pytest/golden script tests | Yes |
| MCP registry validation | `mcp.json`, `mcp/**`, manifests | `wagents mcp audit --check` | Yes |
| MCP security scan | MCP changes | `uvx mcp-scan@latest` | Yes for validated, warn otherwise |
| Harness projection fixtures | adapter changes | golden fixture tests | Yes |
| Docs truth | docs/README/instructions | `wagents docs check` | Yes |
| OpenSpec validation | `openspec/**` | `wagents openspec validate` | Yes |
| Task graph validation | `99-task-graph/**` | `wagents taskgraph validate` | Yes |
| Release package | tags | `wagents package --all` | Yes |

## Non-blocking watch gates

- External index refresh.
- Awesome-list candidate refresh.
- Observability schema drift.
- OpenTelemetry GenAI semconv version check.
