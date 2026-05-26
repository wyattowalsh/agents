# Validation Matrix

| Area | Command | Expected |
| --- | --- | --- |
| OpenSpec | `uv run wagents openspec validate` | Change files and existing specs validate. |
| JSON | `uv run python -m json.tool mcp/mcphub/mcp_settings.json` | Settings parse as JSON. |
| Settings | `bash scripts/mcphub/validate-settings.sh` | Groups reference known servers and no tracked real-looking secrets exist. |
| Local launch scripts | `bash -n scripts/mcphub/*.sh scripts/mcphub/wrappers/*` | Shell syntax passes. |
| Tests | `uv run pytest tests/test_sync_agent_stack.py tests/test_distribution_metadata.py` | MCPHub renderers and registry schema pass. |
| Lint | `uv run ruff check scripts tests wagents` | Python lint passes or unrelated baseline failures are reported. |
| Types | `uv run ty check` | Type check passes or unrelated baseline failures are reported. |
| Runtime | `make mcphub-doctor && make mcphub-smoke` | Requires local `.env.mcphub` secrets and MCPHub startup. |

Docker validation is intentionally not part of this change; the requested local
control plane runs without Docker.
