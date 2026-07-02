# Skills / Plugins Review — Remediation Queue

Generated: 2026-07-01T19:46:37+00:00
Remediation refreshed: 2026-07-02

## Status

All 70 original findings from `planning/manifests/skills-plugins-review-findings.json`
are closed for the reviewed scope.

| Finding set | Status | Closure evidence |
| --- | --- | --- |
| `RV-SP-002` | fixed | `skills/new-project/scripts/check.py` default path completes without the old timeout; `--full` owns the slow OpenSpec validation. |
| `RV-SP-005..054` | fixed | All 50 custom catalog authoring rows now include `trust_tier: "repo-owned"` and `status: "repo-owned"`. |
| `RV-SP-055, RV-SP-057..065` | accepted | External rows now carry explicit global-only/avoid dispositions with `sync_kind: "none"`, `target_agents: []`, and intentionally blank `install_command`. |
| `RV-SP-056` | accepted | `apm-cli` remains an intentional `sync_kind: "external-tool"` entry using `pip install apm-cli`. |
| `RV-SP-001, RV-SP-003, RV-SP-066..068` | fixed | Security-heavy eval coverage increased for `agent-runtime-governance`, `openspec-workflow`, and `orchestrator`. |
| `RV-SP-069` | fixed for original target set | `skill-router` and `i18n-localization` now have five eval cases each. |
| `RV-SP-070` | fixed | `data-pipeline-architect` eval depth is reduced/covered by the current 10-case eval set. |
| `RV-SP-004` | accepted | W2 plugin surfaces were clean; no code remediation was required. |

## Validation Evidence

- `uv run wagents validate` — pass.
- `uv run python skills/new-project/scripts/check.py` — pass.
- `uv run pytest tests/test_authoring_sync.py tests/test_skills_catalog_schemas.py tests/test_catalog_index_parity.py tests/test_external_skills.py tests/test_sync_desired_skills.py -q` — 53 passed.
- `uv run pytest tests/test_eval_adequacy.py tests/test_eval_cli.py tests/test_eval_ci_flagship.py tests/mcp/test_eval_results.py -q` — 53 passed.

## Residual Notes

- Residual eval-depth backlog closed on 2026-07-02: all 65 repo skills now have
  at least five eval cases under `uv run wagents eval coverage --format json`.
  The added cases cover the new skill/plugin maintenance skills that were outside
  the original `RV-SP-069` target set.
