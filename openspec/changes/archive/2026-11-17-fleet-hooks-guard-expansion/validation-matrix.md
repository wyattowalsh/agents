# Validation Matrix

| Check | Command |
|-------|---------|
| Hook unit/integration tests | `uv run pytest tests/hooks/ tests/test_wagents_hook.py tests/test_grok_platform.py tests/test_opencode_hook_bridge.py -q` |
| Repo validate | `uv run wagents validate` |
| Per-harness hooks | `uv run wagents hooks validate --harness all` |
| Sync idempotency | `uv run python scripts/sync_agent_stack.py --check --targets repo` |
| Discovery parity | `uv run python scripts/check_hook_discovery_parity.py` |
| OpenSpec | `uv run wagents openspec validate` |
| Ruff | `uv run ruff check hooks/wagents-hook.py wagents/hooks/` |

## Review closure (C-041d)

| Finding | Status | Proof |
|---------|--------|-------|
| RV-001 | Closed | `before-read-file-guard` alias + bridge `POLICY_MAP.read` |
| RV-002 | Closed | `_deny` opencode branch + integration tests |
| RV-003 | Closed | `_deny` grok-build via `grok_deny_payload` |
| RV-004 | Closed | Shell guard fail-closed on dangerous git when module missing (C-010) |
| RV-005 | Closed | Parity tasks verify-then-checkoff (C-030) |
| RV-006 | Closed | Bridge + harness deny matrix tests |
| RV-007 | Closed | `agents-*.json` removed; apm materialize green |
| RV-008 | Closed | Shell layering docs in hooks hub |
| RV-009 | Closed | Convert lossy docs + tests |
| RV-010 | Closed | `_stop_retry` grok + opencode branches |
