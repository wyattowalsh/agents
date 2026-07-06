# Proposal

## Problem

The managed MCP registry does not include `jupyter-mcp-server`, so harnesses cannot manage Jupyter notebooks (read cells, execute kernels, multimodal outputs) through MCPHub opt-in groups.

## Intent

Add `jupyter-mcp-server` once to the normalized registry using a repo-managed `uvx` stdio wrapper, wire opt-in MCPHub groups (not default `harness` or `tunnel`), and update maintainer docs/KB surfaces.

## Scope

- Add `jupyter-mcp-server` as an enabled stdio MCP server launched via `scripts/mcphub/jupyter-mcp-server-stdio.sh`.
- Add new capability group `notebooks` and opt-in memberships: `coding`, `research`, `review` (bounded read), `heavy`, `credentialed`, `experimental`.
- Refresh generated repo harness MCP surfaces via `scripts/sync_agent_stack.py`.
- Update MCP safety/source documentation for kernel execution, JupyterLab prerequisites, and untrusted notebook content.

## Out Of Scope

- Creating first-party MCP server code under `mcp/jupyter-mcp-server/`.
- Adding to default `harness` or remote `tunnel` groups.
- Repo-managed JupyterLab LaunchAgent or streamable-http `:4040` sidecar.
- Curated external skill catalog row or live `wagents skills sync --apply`.
- Home sync (`--targets home --apply`) without explicit approval.

## Affected Users And Tools

- Users with a local JupyterLab instance who opt into MCPHub `notebooks`, `coding`, or related groups.
- Data science and notebook-centric coding workflows requiring live kernel feedback.

## Risks

- `execute_cell` / `execute_code` run arbitrary code in the Jupyter kernel.
- Requires user-owned `JUPYTER_TOKEN`; must stay in `.env.mcphub` only.
- Multimodal image outputs can inflate context when `ALLOW_IMG_OUTPUT=true`.
- MCP child startup fails when JupyterLab is not running.