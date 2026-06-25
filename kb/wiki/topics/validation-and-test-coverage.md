---
title: Validation And Test Coverage
tags:
  - kb
  - validation
  - tests
aliases:
  - Test coverage map
kind: concept
status: active
updated: 2026-06-25
source_count: 11
---

# Validation And Test Coverage

## Scope

This page maps validation gates and test families. It is not a claim that the full test suite currently passes.

## Summary

The repo has layered validation. `wagents validate` checks a minimal asset structure contract, while packaging checks stricter portability requirements. Generated README and docs have check commands and tests. OpenSpec wrapper behavior, skill inventory, external skill parsing, hooks, evals, catalog integrity, and Nerdbot workflow contracts each have dedicated pytest coverage.

Use this distinction when assessing a change: passing `wagents validate` does not imply portable skill packaging, docs freshness, or live harness sync safety. For Nerdbot KB work, the targeted verification is `uv run --project skills/nerdbot nerdbot inventory --root ./kb` followed by `uv run --project skills/nerdbot nerdbot lint --root ./kb --include-unlayered`.

Hooks and evals are related but distinct: hooks enforce runtime/projection policy, while evals provide skill behavior regression coverage. Eval counts should not be treated as adequate without considering the risk tier of each skill.

**2026-06-25 Wave 05 test cluster:** Dedicated pytest families cover the control plane end-to-end—**31** tests in `test_hooks_cli.py` (list/validate, shorthand hooks, skill-creator `verify.py` integration, `wagents validate` hook checks), **33** in `test_wagents_hook.py` (Codex/Cursor/research policy JSON shapes and shell-write bypass hardening), **22** in `test_eval_cli.py`, **10** in `test_eval_adequacy.py`, **9** in `test_hook_scan.py`, **1** in `test_hook_events_sync.py` (**106** collect-only in the core six files; **108** including Plannotator hook tests). Real-repo smoke tests (`hooks validate`, `eval validate`) anchor CLI gates; adequacy `--strict` exits 0 with `failing_strict: []`.

## Evidence

| Claim | Source | Type | Notes |
|-------|--------|------|-------|
| `wagents validate` has a smaller contract than packaging. | `kb/raw/sources/asset-validation-coverage.md` | raw source note | Key authoring gotcha. |
| Pytest files map to CLI, docs, package, OpenSpec, skills, hooks, evals, catalog, and Nerdbot contracts. | `kb/raw/sources/tests-and-validation.md` | raw source note | Source inventory only. |
| pytest, Ruff, ty, and uv docs are relevant upstream tooling sources. | `kb/raw/sources/external-tooling-docs.md` | external source note | Upstream semantics, not local pass/fail evidence. |
| Nerdbot KB work uses targeted inventory and lint checks. | `kb/raw/sources/nerdbot-runtime-contracts.md`; `kb/raw/extracts/developer-commands-extract.md` | raw source notes | Distinct from full repo CI. |
| Hooks and evals form a control plane for runtime policy and regression coverage. | `kb/raw/sources/hooks-evals-control-source.md` | raw source note | Dedicated hooks/evals source. |
| Skill eval coverage should be interpreted relative to skill risk. | `kb/raw/sources/skill-catalog-risk-eval-coverage.md` | raw source note | Adequacy gap. |
| Hooks/eval pytest cluster: 106 core tests across six files; 108 with Plannotator. | `kb/raw/captures/hooks-tests-cluster-capture-w05.md` | raw capture | Wave 05 cluster inventory. |
| Eval file layout: 602 manifest cases + 189 legacy JSON files → CLI count 791. | `kb/raw/captures/skill-eval-files-capture-w05.md` | raw capture | Manifest vs legacy reconciliation. |
| Ruff scoped `include`/`extend-exclude`; ty `src.include`/`exclude`/`allowed-unresolved-imports`; CI lint+typecheck jobs. | `kb/raw/captures/pyproject-tooling-capture-w11.md` | raw capture | Wave 11 pyproject alignment. |
| uv llms.txt project/workspace reference map. | `kb/raw/extracts/uv-llms-index-extract-w11.md` | external extract | Context for `uv run` / workspace member `mcp/mcphub`. |

## Related

- [[developer-commands]]
- [[skill-authoring-and-validation]]
- [[wagents-cli-and-automation]]
- [[hooks-evals-control-plane]]
- [[skill-catalog-risk-and-eval-coverage]]
- [[known-risks-and-open-gaps]]
