# Validation matrix

| Surface | Command | Success |
| --- | --- | --- |
| Source health | `uv run pytest tests/mcp/test_source_url_health.py tests/test_pinned_httpx_client.py tests/test_ssrf_policy.py -q` | all pass, no network |
| Source health types | `uv run ty check mcp/source-url-health tests/mcp/test_source_url_health.py tests/test_pinned_httpx_client.py tests/test_ssrf_policy.py` | zero diagnostics |
| Source health wheel | build wheel in a temporary directory and import it in an isolated environment | `server` and `ssrf` import |
| Nerdbot | `uv run pytest tests/test_nerdbot_contract_helpers.py tests/test_nerdbot_workflows.py tests/test_nerdbot_package.py tests/test_nerdbot_schema_contracts.py tests/test_nerdbot_scripts.py -q` | all pass |
| Nerdbot skill | `(cd skills/nerdbot && uv run python scripts/check.py)` | exit 0, portable package |
| Package hardening | focused Skill Creator/package tests | all adversarial cases pass |
| Eval inventory | focused eval CLI/validator tests and `uv run wagents eval list --format json` | Nerdbot counted once; legacy fixtures unchanged |
| Toolkit parity | `uv run pytest tests/test_skill_bundled_toolkit.py -q` | eligible copies match canonical source |
| OpenSpec | `uv run wagents openspec validate --format json` | target change valid; unrelated active-change failures reported separately |
| Projection | `uv run python scripts/sync_agent_stack.py --targets repo --check` | no drift |
| Docs | `uv run wagents docs generate --check --no-installed` and `uv run wagents docs build` | pass after source quiescence |
| Full repository | repo validation, full pytest, Ruff, Ty, lock checks | no target-caused failures; unrelated failures reported exactly |
