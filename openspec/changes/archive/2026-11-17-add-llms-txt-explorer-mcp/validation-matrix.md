# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| OpenSpec artifacts | `uv run wagents openspec validate` | Change artifacts validate | After tasks complete. |
| Registry parity | `just mcphub-generate-check` | Settings match registry | Regenerate before check if needed. |
| Settings invariants | `bash scripts/mcphub/validate-settings.sh` | exit 0 | Bearer auth and group membership valid. |
| Repo sync | `uv run python scripts/sync_agent_stack.py --targets repo --apply` | MCP mirrors updated | Do not hand-edit generated surfaces. |
| Registry tests | `uv run pytest tests/test_llms_txt_explorer_registry.py tests/test_sync_agent_stack.py::test_repo_workflow_groups_and_bounded_clients -q` | pass | Bounded harness + tunnel exclusion. |
| Asset validation | `uv run wagents validate` | pass | Harness minimal set includes bounded llms-txt-explorer. |
| Docs regen | `uv run python -c "from wagents.docs_compose_regen_configs import regen_configs_batch; regen_configs_batch(config_stems=['mcp-registry'])"` | mcp-registry.mdx embed refreshed | Update HAND-MAINTAINED prose separately. |
| Package probe | `bash scripts/mcphub/llms-txt-explorer-stdio.sh` | stdio probe starts | Expect GitHub catalog fetch on cold start. |

## Blockers

- None after bounded-harness remediation.

## Deferred Checks

- Home sync (`--targets home --apply`) when OpenCode ConfigDropError is resolved
- Runtime MCPHub tools/list smoke after hub restart
- Upstream SSRF hardening PR to thedaviddias/mcp-llms-txt-explorer