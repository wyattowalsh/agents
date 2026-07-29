# Validation Matrix: remediate-rv-skill-docs-contracts

| ID | Surface | Command | Expected Result | Notes |
| --- | --- | --- | --- | --- |
| V-001 | RV-003 process lifecycle | `uv run pytest -q tests/test_candidate_cli_canaries.py tests/test_candidate_plugin_canaries.py -k 'timeout or process_group or cleanup'` | Timed-out child and descendant receive group TERM, bounded wait, group KILL when needed, then child reap and stdout/stderr drain | Lifecycle proof only; no sandbox claim |
| V-002 | RV-003 receipt dependency | `uv run pytest -q tests/test_candidate_runtime_activation.py::test_behavioral_receipt_regeneration_requires_lifecycle_gate` | Behavioral receipt regeneration is rejected while V-001 is missing, stale, or failing | Runs before any candidate behavioral receipt writer |
| V-003 | RV-009 YAML semantics | `uv run python skills/skill-package-manifest-enricher/scripts/check.py` | Folded/chomped YAML scalars parse with real YAML semantics; preview is non-mutating | Portable check must not import repo `wagents` |
| V-004 | RV-009 target derivation | `uv run python skills/skill-package-manifest-enricher/scripts/check.py` | Focused catalog-source, sync-source, and neither-source fixtures derive targets from supplied portable metadata with source digest; unavailable input emits explicit unavailable state and no hardcoded targets | Additive manifest keys preserved |
| V-005 | RV-010 pure validation | `uv run pytest -q tests/test_docs_reports.py tests/test_docs.py -k 'graph or snapshot or stale or check'` | Check/validation code performs no writes or clock reads; equal inputs and date are byte-stable | Existing graph history stores dates |
| V-006 | RV-010 explicit mutation | `uv run wagents docs generate --no-installed --snapshot-date 2026-07-29` followed by `uv run wagents docs generate --no-installed --check` | Explicit UTC `YYYY-MM-DD` is deterministic; omitted mutation option captures UTC date once at the CLI boundary; check reads no clock; invalid supplied date fails before writing | Run once in the serialized generator lane |
| V-007 | RV-012 taxonomy | `uv run pytest -q tests/test_site_model.py tests/test_docs_catalog.py tests/test_docs.py tests/test_readme.py -k 'agent or harness or support or homepage or readme'` | Exact managed six, exact Skills CLI-native five, separately labeled MCP-only/hybrid rows, and homepage/README row-count agreement | Assert identities and counts |
| V-008 / RV-007 | AITK/Crush proof only | `uv run pytest -q tests/test_sync_agent_stack.py -k 'crush or aitk'` | AITK entries are selected with `render_flat_mcp(..., harness="crush")`, form a flat map, and use `type: stdio`; no `render_client_mcp` regression | No implementation ownership in this change |
| V-009 / RV-011 | Reddit MCP Buddy proof only | `uv run pytest -q tests/test_reddit_mcp_buddy_registry.py` | Exact allowlist is `browse_subreddit`, `search_reddit`, `get_post_details`, `user_analysis`, `reddit_explain`; no wildcard or `tools_allow_all` | Any extra/missing tool fails |
| V-010 / RV-013 | Retirement proof only | `uv run pytest -q tests/test_retire_harness_targets.py` and `uv run python scripts/retire_harness_targets.py --check`, plus the bounded generated-surface semantic scan defined by `remove-gemini-antigravity-copilot` | Active source/generated surfaces reject retired managed IDs and `https://github.com/google/gemini-cli`; explicit historical/change-control and unrelated keep-set remains | Raw source-name substrings are not endorsement by themselves |
| V-011 | Asset validation | `uv run wagents validate` | Portable skills, agents, registries, and quarantine policy pass | Run after source changes |
| V-012 | README | `uv run wagents readme --check` | README grouping/counts match generated source | Regenerate first in owning lane when stale |
| V-013 | Docs | `uv run wagents docs generate --no-installed --check` and scheduled docs tests/build | Generated graph, homepage, support, catalog, and report surfaces are current | Do not overlap a live generator |
| V-014 / RV-008 | Final APM gate | `uv run wagents apm refresh-lock --check` | Dry-run reports no deployed-file path/hash drift | Must be the last gate after every generator |
| V-015 | Targeted OpenSpec | `npx -y @fission-ai/openspec@latest validate remediate-rv-skill-docs-contracts --type change --strict --json --no-interactive` | New change is strict-valid | Run before implementation handoff |
| V-016 | Full OpenSpec | `uv run wagents openspec validate --format json` | All specs and changes validate | Final planning proof |

## Blockers

- Candidate behavioral receipt regeneration remains blocked until V-001 and
  V-002 pass.
- Docs and README outputs are shared, dirty generated surfaces; only the owning
  serialized generator lane may refresh them.
- V-014 cannot run until all docs, README, sync, materialization, and other APM
  projection writers finish.

## Deferred Checks

- Live skill installation and production actions remain out of scope.
- Candidate behavioral receipt regeneration is a downstream action after this
  change's process-lifecycle gate; it is not proof of planning completion.
- No generated OpenSpec downstream artifacts are committed.
