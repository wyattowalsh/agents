# MCPHub CLI Cheat Sheet

## Repo recipes (preferred)

```bash
just mcphub-up
just mcphub-down
just mcphub-doctor
just mcphub-smoke
just mcphub-generate
just mcphub-generate-check
just mcphub-validate
just mcphub-openapi
```

## Bundled operator preflight

```bash
bash skills/mcphub-operator/scripts/preflight.sh
bash skills/mcphub-operator/scripts/preflight.sh --cwd /path/to/agents
```

## Live hub CLI (when `just mcphub-up` is healthy)

Use the upstream MCPHub CLI against `http://127.0.0.1:46683` with bearer auth from `.env.mcphub`:

- List groups and servers configured in the running hub
- Inspect tools for a group or server endpoint
- Export OpenAPI (`just mcphub-openapi`)

Pass `Authorization: Bearer $MCPHUB_BEARER_TOKEN` on `/mcp` routes. Do not enable `$smart` endpoints — Smart Routing stays off in tracked settings.