# MCP server change task template

Use this checklist in OpenSpec `tasks.md` for third-party or first-party MCP registry additions.

## Required tasks

- [ ] Audit upstream server (tools, transport, secrets, network egress) — evidence in `audit-bundle.json` when non-trivial.
- [ ] **Delegate capability matrix** to `mcp-capability-mapper` (or document explicit bypass rationale in the change design).
- [ ] Add stdio wrapper under `scripts/mcphub/<server>-stdio.sh` when MCPHub-managed.
- [ ] Register server + groups in `config/mcp-registry.json` with bounded `harness`/`tunnel` policy.
- [ ] Add registry pytest (`tests/test_<server>_registry.py`).
- [ ] Regenerate `mcp/mcphub/mcp_settings.json` and sync repo harness MCP projections.
- [ ] Update maintainer docs (`docs/ai-tools/mcphub.md`, group-picker, public MCP pages as needed).
- [ ] Run validation matrix (`wagents validate`, mcphub-generate-check, targeted pytest, sync --check).

## Bypass gate

If the change skips `mcp-capability-mapper`, record in `design.md`:

- Why manual mapping was sufficient (e.g., single-tool server, prior audited change).
- Who verified registry ↔ docs ↔ group parity.
- Follow-up item if bypass was emergency-only.