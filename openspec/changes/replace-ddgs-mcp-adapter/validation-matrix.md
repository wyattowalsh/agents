# Validation Matrix

| Lane | Command | Expected |
| --- | --- | --- |
| Registry contract | `uv run pytest -q tests/test_ddgs_registry.py` | DDGS launches as `uvx --from ddgs[mcp] ddgs mcp` |
| Response parser | `uv run pytest -q tests/test_mcphub_mcp_response.py` | JSON, SSE, header, lifecycle-result, tool-shape, pagination, and assertion fixtures pass |
| MCPHub settings | `uv run python scripts/generate_mcphub_settings.py --check` | tracked settings match registry |
| Repo projection | `uv run python scripts/sync_agent_stack.py --targets repo --check` | harness projections have no registry drift |
| Docs config render | `uv run wagents docs compose --regen-configs --config mcp-registry --dry-run` | registry embed renders without writing |
| Shell syntax | `bash -n scripts/mcphub/smoke.sh` | lifecycle smoke script parses |
| Shell lint | `shellcheck -x scripts/mcphub/smoke.sh` | lifecycle smoke script passes ShellCheck |
| OpenSpec | `uv run wagents openspec validate` | all changes and specs validate |
| Runtime smoke | `just mcphub-smoke` | root route succeeds, `/mcp/ddgs` equals the exact six-tool set, and `/mcp/harness` contains all six |

## Package Provenance Probe

Observed during the read-only upstream audit on 2026-07-08: `ddgs==9.14.4`; `ddgs/api_server/mcp.py` defines six `@mcp.tool()` functions for text, images, news, videos, books, and content extraction. Runtime acceptance still requires the MCPHub route smoke above; source inspection alone does not satisfy it.
