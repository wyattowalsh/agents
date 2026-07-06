# Design

## Approach

Add `jupyter-mcp-server` directly to `config/mcp-registry.json` using the same registry schema as existing uvx-managed stdio MCP servers. Launch through a repo wrapper script that pins `jupyter-mcp-server==1.0.2` before `uvx jupyter-mcp-server`.

Keep the server enabled globally but exclude it from default client profiles (`harness`, `tunnel`). Expose through opt-in capability and workflow groups only.

## Data And Control Flow

1. User starts JupyterLab locally with a token.
2. `.env.mcphub` supplies `JUPYTER_URL`, `JUPYTER_TOKEN`, and optional `ALLOW_IMG_OUTPUT`.
3. MCPHub spawns `jupyter-mcp-server-stdio.sh` → `uvx jupyter-mcp-server`.
4. Harnesses reach tools via opt-in group endpoints (e.g. `/mcp/notebooks`).

## Integration Points

- `jupyter-mcp-server`:
  - `transport`: `stdio`
  - `command`: `bash`
  - `args`: `["${REPO_ROOT}/scripts/mcphub/jupyter-mcp-server-stdio.sh"]`
- Wrapper launches:
  - `uvx --from jupyter-mcp-server==1.0.2 jupyter-mcp-server`
  - User overrides via `.env.mcphub` using `MCPHUB_JUPYTER_PACKAGE` (not committed)

## Group Membership

| Group | Shape |
|-------|-------|
| `notebooks` | full server |
| `coding` | full server |
| `research` | bounded read tools only |
| `review` | bounded read tools only |
| `heavy` | full server |
| `credentialed` | full server |
| `experimental` | full server |
| `harness`, `tunnel`, `shared-read` | excluded |

Bounded read tools: `list_files`, `list_kernels`, `list_notebooks`, `read_notebook`, `read_cell`.

## Alternatives Rejected

- Streamable HTTP on `:4040` with `MCP_TOKEN`: rejected; dual auth sidecar does not match MCPHub stdio child model.
- Default `harness` membership: rejected; kernel execution and schema cost violate bounded default policy.
- Repo-managed JupyterLab launch: deferred; Jupyter runtime is user-owned and environment-specific.
- Docker `datalayer/jupyter-mcp-server`: deferred; uvx matches repo Python fleet conventions.

## Migration Or Compatibility Notes

No compatibility shim needed. Existing unmanaged user MCP servers are preserved by merge logic in sync.