---
title: Scripts And Validation Tooling
tags:
  - kb
  - validation
  - scripts
aliases:
  - Validation scripts
kind: concept
status: active
updated: 2026-06-23
source_count: 2
---

# Scripts And Validation Tooling

## Summary

`wagents validate` delegates to `scripts/validate/validate_repo.py`, which runs collectors for skills, agents, MCP, hooks, path portability, MCP registry contributor policy, and quarantine checks against the catalog index and legacy external-skills MD. Sync drift detection uses `scripts/sync_agent_stack.py --check` (via `scripts/check_agent_stack.py` wrapper).

## Why it matters

- Validation scope is broader than skill frontmatter alone; quarantine and portability are part of the same gate.
- Hook lint scripts use narrower Python allowlists than CI ruff/ty; local hook failures may not match CI.
- Several specialized validators exist but are not all wired into automation.

## Current shape

| Tool | Role |
|------|------|
| `scripts/validate/validate_repo.py` | Aggregator invoked by `wagents validate` |
| `scripts/validate/collectors/*` | Per-domain checks including quarantine dual-read |
| `scripts/sync_agent_stack.py` | Canonical sync engine with `--check`/`--apply` |
| `scripts/check_agent_stack.py` | Thin `--check --targets all` wrapper |
| `scripts/validate_codex_config.py` | Codex TOML schema check (orphaned from CI) |
| `hooks/lint-check.sh` | Local ruff/ty with hard-coded allowlists |

## Constraints and edge cases

- `scripts/validate/` is excluded from `ty` src and uses runtime `sys.path` bootstrap to asset_toolkit.
- Sync rollback contract in `config-transaction-registry.json` exceeds what sync code implements today.

## Provenance

| Claim or section | Raw or canonical material | Notes |
|------------------|---------------------------|-------|
| Script inventory and gaps | `kb/raw/sources/scripts-validation-tooling-source.md` | Primary source |
| Asset validation vs packaging | `kb/raw/sources/asset-validation-coverage.md` | Complementary |

## Related wiki pages

- [[validation-and-test-coverage]]
- [[ci-and-release-workflows]]
- [[sync-transaction-safety]]

## Open questions

- Wire `validate_codex_config.py` into CI or document explicit non-use.